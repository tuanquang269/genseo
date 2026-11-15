import json,os,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
slug='creatine-gummies-vs-bcaa-the-us-verdict'
tax=json.loads((root/'personas/taxonomy.json').read_text())
angles={a['id']:' — '.join(x for x in (a['phrase'],a.get('frame_hint')) if x) for a in tax['face_angle_values']}
ref=str(root/'personas/f3039-bl-02/ref.jpg')
hero=f'''Bright realistic editorial hero, landscape, over-shoulder shot: camera peers over an unrecognizable foreground companion's shoulder at the approved person beside a home workout planning table. Approved person's face clearly visible, wearing a rust-orange sports top, calm attentive expression. Their eyes look at the companion, not the lens. {angles['3q-left+chin-up']}. Bright-green stand-up pouch of Wellness Nest FusiForce Creatine Monohydrate Gummies stands label-forward on table beside person, large enough for thumbnail legibility. Vertical white Wellness Nest wordmark and W logo at left, white FusiForce pill badge, Green Apple flavor tag, 90 gummies footer, exact reference packaging. Hands rest on lap, no contact with pack. Natural bright daylight, real skin texture, warm wood and a folded training mat. NEGATIVE: no hands touching the pouch, no invented face, no plastic skin, no glassy eyes, no waxy face, no caption, no watermark, no invented label layout, no jar, no stat badges, no visible companion face.'''
def ugc(scene,subject,env,light,face=''):
 return f'''SPEC: Photorealistic casual smartphone photo, landscape, at most 1K resolution.
FIDELITY LOCK: Exact reference bright-green stand-up pouch of Wellness Nest FusiForce Creatine Monohydrate Gummies; vertical white Wellness Nest wordmark and W logo at left, white FusiForce pill badge, Green Apple flavor tag, 90 gummies footer. No loose gummies.
REFERENCE: Curated real pack reference; {('approved original persona reference, same identity as hero' if face else 'no face reference, no recognizable face anywhere')}.
SCENE / MOMENT: {scene}
DEVICE & CAMERA: Handheld phone snapshot, slightly imperfect angle, natural depth of field, mild motion softness, not a studio shoot.
SUBJECT & BODY: {subject} {face}
LIGHTING: {light}
ENVIRONMENT DETAIL: {env}
STYLE / IMPERFECTION: Subtle grain, unretouched surface wear, muted phone-JPEG colours, amateur snapshot energy, no HDR gloss.
NEGATIVE: no beaming model staring at camera, no sterile marble countertop with citrus slices, no floating ingredients, no teal-orange grade, no studio softbox, no plastic skin, no glassy eyes, no waxy face, no watermark, no caption, no on-image text, no invented label layout, no stat-percentage badges on package, no hands touching the pouch.'''
items=[('hero',hero,False,'3q-left+chin-up'),('training-log',ugc('Person seated sideways on a home workout-room bench, writing in a blank training notebook after exercise; pouch stands on the bench end label-forward.','Same approved person, rust-orange top, shoulders relaxed; eyes down at hands writing, not at lens.','A rolled green towel and closed water bottle beside the notebook.','Available side-window daylight, slightly warm white balance.',angles['profile-right+level']),True,'profile-right+level'),('meal-prep',ugc('At a small breakfast-bar edge, person slides a bowl of yogurt toward a seat; FusiForce pouch stands further along counter label-forward.','Only forearms and torso cropped below neck; relaxed everyday motion, no face.','Plain yogurt bowl, spoon, muted green napkin; modest ordinary kitchen, not marble.','Soft morning window light with slightly uneven exposure.'),True,None),('gym-bag',ugc('At an entryway shoe bench, person zips a gym bag before leaving; FusiForce pouch stands on bench label-forward.','Hands at bag zipper, torso cropped below shoulders, no recognizable face.','Canvas gym bag, worn trainers below bench, green jacket hanging off edge.','Available hallway daylight with gentle shadow and imperfect white balance.'),True,None)]
for name,prompt,isugc,angle in items:
 cmd=[sys.executable,str(root/'scripts/article_images.py'),'--slug',slug,'--name',name,'--prompt',prompt,'--product-ref','fusiforce-creatine-gummies','--qc']
 if isugc:cmd+=['--ugc']
 if angle:cmd+=['--persona-ref',ref,'--face-angle',angle]
 print('GENERATING',name,flush=True)
 p=subprocess.run(cmd,env={**os.environ,'GENSEO_NO_FACE':'0'})
 if p.returncode:sys.exit(p.returncode)
