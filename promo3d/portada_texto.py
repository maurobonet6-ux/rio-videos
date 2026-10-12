# Texto de la portada: título, frase y marca sobre el render de portada.py. Uso: python3.11 promo3d/portada_texto.py RENDER.png SALIDA.jpg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, sys
F='/usr/share/fonts/opentype/inter/InterDisplay-'; BL,BO=F+'Black.otf',F+'Bold.otf'
W,H=1080,1920; BLANCO=(245,245,247); ROJO=(229,48,74)
a=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float); y=np.arange(H)[:,None,None]; xx=np.arange(W)[None,:,None]
k=1-0.35*np.exp(-((y-1620)/170.0)**2); vin=1-0.35*(((xx-W/2)/(W/2))**2*0.6+((y-H/2)/(H/2))**2*0.4)
c=Image.fromarray((a*k*vin).clip(0,255).astype('uint8')).convert('RGBA')
def txt(t,y,f,col,sombra=True,brillo=False):
    d=ImageDraw.Draw(c); w=d.textlength(t,font=f); x=(W-w)/2
    if brillo:
        g=Image.new('RGBA',(W,H)); ImageDraw.Draw(g).text((x,y),t,font=f,fill=(229,48,74,150)); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(28)))
    if sombra:
        s=Image.new('RGBA',(W,H)); ImageDraw.Draw(s).text((x,y+6),t,font=f,fill=(0,0,0,210)); c.alpha_composite(s.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(c).text((x,y),t,font=f,fill=col)
txt('Los mejores',505,ImageFont.truetype(BL,84),BLANCO)
tam=200
while ImageDraw.Draw(c).textlength('ESTUDIAN',font=ImageFont.truetype(BL,tam))>W*0.86: tam-=4
txt('ESTUDIAN',595,ImageFont.truetype(BL,tam),ROJO,brillo=True)
txt('antes de sentarse a la mesa',1575,ImageFont.truetype(BO,50),BLANCO)
fl=ImageFont.truetype(BL,70); d=ImageDraw.Draw(c); w1=d.textlength('R',font=fl); w2=d.textlength('ÍO',font=fl); x=(W-w1-w2)/2; yl=1700
s=Image.new('RGBA',(W,H)); ImageDraw.Draw(s).text((x,yl+6),'RÍO',font=fl,fill=(0,0,0,200)); c.alpha_composite(s.filter(ImageFilter.GaussianBlur(12)))
d=ImageDraw.Draw(c); d.text((x,yl),'R',font=fl,fill=BLANCO); d.text((x+w1,yl),'ÍO',font=fl,fill=ROJO)
txt('ESTRATEGIA DE PÓKER',1790,ImageFont.truetype(BO,30),(205,205,210),sombra=False)
c.convert('RGB').save(sys.argv[2],quality=94)
