import sys
from PIL import Image, ImageDraw
a,b,out,colw=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4])
A=Image.open(a).convert("RGB"); B=Image.open(b).convert("RGB")
def sc(im): r=colw/im.width; return im.resize((colw,int(im.height*r)))
A=sc(A); B=sc(B); H=max(A.height,B.height)+40
S=Image.new("RGB",(colw*2+30,H),"#ddd"); d=ImageDraw.Draw(S)
S.paste(A,(0,40)); S.paste(B,(colw+30,40))
d.text((8,12),"REFERENCE  "+a.split("/")[-1],fill="black"); d.text((colw+38,12),"OURS (GenSeo replica)  "+b.split("/")[-1],fill="black")
S.save(out,quality=72); print(out,S.size)
