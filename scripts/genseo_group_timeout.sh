#!/bin/bash
# Run CMD in its own session. If it is still running after SECONDS, TERM and then KILL
# that process group (the bash ticket runner and Claude children that stayed with it).
#
# `perl -e 'alarm N; exec CMD'` arms ITIMER_REAL and replaces perl with CMD. The signal
# hits only that pid. run_ticket_headless.sh dies and Claude, in the same process group,
# keeps publishing while the daily wrapper starts the next ticket.
#
# This process stays the parent. The child calls setsid, so its PGID is its PID and the
# daily wrapper is not in the group. Timeout, and TERM/HUP/INT delivered to this waiter,
# are forwarded to the group. GENSEO_TIMEOUT_GRACE_SEC (default 2) is the pause between
# TERM and KILL so a child that ignores TERM still dies. The waiter polls: Perl's safe
# signals do not run a handler until a blocking waitpid returns, which would be the
# ticket's own exit.
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
use POSIX qw(setsid :sys_wait_h);
use Errno qw(EINTR);

my $secs = shift @ARGV;
my $grace = shift @ARGV;
die "genseo_group_timeout: missing command\n" unless defined $secs && defined $grace && @ARGV;

my $timed_out = 0;
my $forward = 0;
my $pid = fork();
die "genseo_group_timeout: fork: $!\n" unless defined $pid;
if ($pid == 0) {
  setsid() or exit 125;
  exec @ARGV or exit 127;
}

$SIG{ALRM} = sub { $timed_out = 1 };
$SIG{TERM} = sub { $forward = 15 };
$SIG{HUP}  = sub { $forward = 1 };
$SIG{INT}  = sub { $forward = 2 };

alarm $secs;
# Perl's safe signals defer the handler until a blocking waitpid returns, so an
# alarm or SIGTERM during waitpid would not run until the ticket exited. Poll.
my $got = -1;
while (1) {
  $got = waitpid($pid, WNOHANG);
  last if $got == $pid;
  last if $timed_out || $forward;
  if ($got < 0 && $! != EINTR) { last; }
  select undef, undef, undef, 0.2;
}
alarm 0;

if (($timed_out || $forward) && $got != $pid && $pid > 1) {
  if ($timed_out) {
    warn "genseo_group_timeout: timeout ${secs}s, signaling process group $pid\n";
  } else {
    warn "genseo_group_timeout: forwarding signal $forward to process group $pid\n";
  }
  kill 'TERM', -$pid;
  my $deadline = time() + $grace;
  while ($got != $pid && time() < $deadline) {
    my $w = waitpid($pid, WNOHANG);
    if ($w == $pid || $w < 0) { $got = $w; last; }
    select undef, undef, undef, 0.05;
  }
  kill 'KILL', -$pid;
  waitpid($pid, 0) if $got != $pid;
  exit 124 if $timed_out;
  exit 128 + $forward;
}

exit 1 if $got != $pid;
my $st = $?;
exit(128 + ($st & 127)) if $st & 127;
exit($st >> 8);
PERL
