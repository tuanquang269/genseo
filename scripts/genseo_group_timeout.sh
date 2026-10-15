#!/bin/bash
# Run CMD in its own session. If it is still running after SECONDS, TERM and
# then KILL every descendant, then that process group.
#
# The deadline is elapsed CLOCK_MONOTONIC from the start of this wait. It is
# not alarm(2) and not wall-clock time(). Perl delivers SIGALRM only between
# opcodes, and on macOS a pending SIGALRM restarts select(2) instead of
# running the handler (Time::HiRes: the alarm and the select add, and mixing
# an itimer with sleep has hung under ktrace). The 2026-10-12 article run
# still had `perl - 5400 2` polling at 21:06 ICT, 55 minutes after the
# 90-minute cap, with no timeout line and state/daily.lock still held. A
# wall-clock deadline would also slip if NTP stepped the clock backward.
#
# `kill` of the negative process-group id only reaches processes that stayed
# with the session leader. This script's child calls setsid; Claude and its
# workers call setsid again and leave. A group kill reparents them to launchd
# and the TCP connect keeps running. A blocking waitpid after a missed kill
# of the leader never returns, so the lock stays held. Descendants are
# collected by parent pid first (Linux /proc, otherwise ps), signaled by
# positive pid, then the process group is signaled for anyone who joined it
# after the snapshot. Reaping uses WNOHANG only.
#
# GENSEO_TIMEOUT_GRACE_SEC (default 2) is the pause between TERM and KILL.
# GENSEO_TIMEOUT_LOG, when set, receives the same line as stderr. The article
# log stays block-buffered until the writer exits, so the daily log is where
# the timeout line has to land.
#
# A retry backoff is sleep inside a descendant (Python time.sleep, or a child
# that ignores TERM and sleeps). The snapshot is taken before the first
# signal, and KILL follows TERM, so that sleep cannot outlive the cap. The
# same walk covers a setsid grandchild that is still parented under the tree.
#
# Exit: CMD's status, 124 on timeout, 128+signal when this waiter is signaled,
# 125 if setsid fails, 127 if CMD cannot be executed.
# Usage: genseo_group_timeout.sh SECONDS CMD [ARGS...]
set -u
if [ "$#" -lt 2 ]; then
  echo "usage: genseo_group_timeout.sh SECONDS CMD [ARGS...]" >&2
  exit 2
fi
secs=$1
shift
case "$secs" in
  ''|*[!0-9]*|0)
    echo "genseo_group_timeout: SECONDS must be a positive integer" >&2
    exit 2
    ;;
esac
grace="${GENSEO_TIMEOUT_GRACE_SEC:-2}"
case "$grace" in
  ''|*[!0-9]*)
    echo "genseo_group_timeout: bad GENSEO_TIMEOUT_GRACE_SEC" >&2
    exit 2
    ;;
esac
exec perl - "$secs" "$grace" "$@" <<'PERL'
use strict;
use warnings;
use POSIX qw(setsid _exit :sys_wait_h);
use Errno qw(EINTR);

my $secs = shift @ARGV;
my $grace = shift @ARGV;
die "genseo_group_timeout: missing command\n" unless defined $secs && defined $grace && @ARGV;
$secs += 0;
$grace += 0;

my $have_hires = 0;
my $clock;
eval {
  require Time::HiRes;
  $clock = Time::HiRes::CLOCK_MONOTONIC();
  my $sample = Time::HiRes::clock_gettime($clock);
  die "no monotonic clock\n" if !defined $sample;
  $have_hires = 1;
};

sub mono {
  return Time::HiRes::clock_gettime($clock) if $have_hires;
  return time;
}

sub pause_for {
  my ($sec) = @_;
  return if !defined $sec || $sec <= 0;
  if ($have_hires) {
    Time::HiRes::sleep($sec);
    return;
  }
  select undef, undef, undef, $sec;
}

sub note {
  my ($msg) = @_;
  $msg .= "\n" if $msg !~ /\n\z/;
  warn $msg;
  my $path = $ENV{GENSEO_TIMEOUT_LOG};
  return if !defined $path || $path eq "" || $path =~ /\0/;
  if (open my $fh, ">>", $path) {
    print {$fh} $msg;
    close $fh;
  }
}

sub ppid_map {
  my %ppid;
  if (opendir my $dh, "/proc") {
    while (my $ent = readdir $dh) {
      next if $ent !~ /^[0-9]+$/;
      next if !open my $fh, "<", "/proc/$ent/status";
      while (my $line = <$fh>) {
        if ($line =~ /^PPid:\s+([0-9]+)/) {
          $ppid{$ent + 0} = $1 + 0;
          last;
        }
      }
      close $fh;
    }
    closedir $dh;
    return %ppid if %ppid;
  }
  for my $cmd (
    [qw(ps -ax -o pid=,ppid=)],
    [qw(/bin/ps -ax -o pid=,ppid=)],
    [qw(/usr/bin/ps -ax -o pid=,ppid=)],
  ) {
    %ppid = ();
    open my $ps, "-|", @$cmd or next;
    while (my $line = <$ps>) {
      if ($line =~ /^\s*([0-9]+)\s+([0-9]+)\s*$/) {
        $ppid{$1 + 0} = $2 + 0;
      }
    }
    close $ps;
    return %ppid if %ppid;
  }
  return %ppid;
}

# Seed plus every process whose parent chain reaches the seed. A setsid()
# grandchild stays in this set until its parent dies; the caller must keep
# the list from before the first signal.
sub descendant_pids {
  my ($seed) = @_;
  return () if !$seed || $seed <= 1 || $seed == $$;
  my %ppid = ppid_map();
  my @out = ($seed);
  my %seen = ($seed => 1);
  my $guard = 0;
  my $grew = 1;
  while ($grew && $guard++ < 40) {
    $grew = 0;
    for my $pid (keys %ppid) {
      next if $seen{$pid} || $pid <= 1 || $pid == $$;
      my $parent = $ppid{$pid} || 0;
      next if !$seen{$parent};
      $seen{$pid} = 1;
      push @out, $pid;
      $grew = 1;
    }
  }
  return @out;
}

sub still_alive {
  my ($p) = @_;
  return 0 if !$p || $p <= 1 || $p == $$;
  return kill 0, $p;
}

sub signal_pids {
  my ($sig, @pids) = @_;
  my %seen;
  for my $p (@pids) {
    next if !$p || $p <= 1 || $p == $$ || $seen{$p}++;
    kill $sig, $p;
  }
}

# Portable process-group signal: negative signal name, positive pgrp.
# kill 'TERM', -$pid depends on kill(2) treating a negative pid as a group,
# which perlfunc documents as non-portable. kill '-TERM', $pid uses killpg
# where the platform has it.
sub signal_group {
  my ($sig, $pgrp) = @_;
  return if !$pgrp || $pgrp <= 1;
  my $flag = ($sig =~ /^-/) ? $sig : "-$sig";
  kill $flag, $pgrp;
}

my $timed_out = 0;
my $forward = 0;
my $pid = fork();
die "genseo_group_timeout: fork: $!\n" unless defined $pid;
if ($pid == 0) {
  setsid() or _exit 125;
  exec @ARGV;
  _exit 127;
}

$SIG{TERM} = sub { $forward = 15 };
$SIG{HUP}  = sub { $forward = 1 };
$SIG{INT}  = sub { $forward = 2 };

my $t0 = mono();
my $got = -1;
while (1) {
  $got = waitpid($pid, WNOHANG);
  last if $got == $pid;
  last if $forward;
  if (mono() - $t0 >= $secs) { $timed_out = 1; last; }
  if ($got < 0 && $! != EINTR) { last; }
  pause_for(0.2);
}

if (($timed_out || $forward) && $got != $pid && $pid > 1) {
  my @wave = descendant_pids($pid);
  @wave = ($pid) if !@wave;
  my $n = scalar @wave;
  if ($timed_out) {
    note("genseo_group_timeout: TIMEOUT after ${secs}s, signaling process group $pid ($n in the tree)\n");
  } else {
    note("genseo_group_timeout: forwarding signal $forward to process group $pid ($n in the tree)\n");
  }
  signal_pids("TERM", @wave);
  signal_group("TERM", $pid);
  my $g0 = mono();
  while ($got != $pid && mono() - $g0 < $grace) {
    my $w = waitpid($pid, WNOHANG);
    if ($w == $pid || $w < 0) { $got = $w; last; }
    pause_for(0.05);
  }
  my @kill_set = @wave;
  for my $p (@wave) {
    next unless still_alive($p);
    push @kill_set, descendant_pids($p);
  }
  signal_pids("KILL", @kill_set);
  signal_group("KILL", $pid);
  my $r0 = mono();
  while ($got != $pid && mono() - $r0 < 2) {
    my $w = waitpid($pid, WNOHANG);
    if ($w == $pid || $w < 0) { $got = $w; last; }
    pause_for(0.05);
  }
  exit 124 if $timed_out;
  exit 128 + $forward;
}

exit 1 if $got != $pid;
my $st = $?;
exit(128 + ($st & 127)) if $st & 127;
exit($st >> 8);
PERL
