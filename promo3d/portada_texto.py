# Texto de la portada: título, frase y marca sobre el render de portada.py. Uso: python3.11 promo3d/portada_texto.py RENDER.png SALIDA.jpg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, sys
F='/usr/share/fonts/opentype/inter/InterDisplay-'; BL,BO=F+'Black.otf',F+'Bold.otf'
W,H=1080,1920; BLANCO=(245,245,247); ROJO=(229,48,74)
a=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float); y=np.arange(H)[:,None,None]; xx=np.arange(W)[None,:,None]
k=1-0.35*np.exp(-((y-1620)/170.0)**2); vin=1-0.35*(((xx-W/2)/(W/2))**2*0.6+((y-H/2)/(H/2))**2*0.4)
a=a*k*vin/255; lum=(a@np.array([0.2126,0.7152,0.0722]))[...,None]
a=a+(1-lum)**4*np.array([0.022,0,0.006]); a=a*(1+lum**2*np.array([0.03,0,-0.035]))   # etalonaje: negros con punto rojo, luces cálidas
c=Image.fromarray((a*255).clip(0,255).astype('uint8')).convert('RGBA')
def ancho(t,f,trk): return sum(ImageDraw.Draw(c).textlength(ch,font=f) for ch in t)+trk*f.size*(len(t)-1)
def letras(d,x,y,t,f,fill,trk):
    for ch in t: d.text((x,y),ch,font=f,fill=fill); x+=d.textlength(ch,font=f)+trk*f.size
def txt(t,y,f,col,sombra=True,brillo=False,trk=0.0):
    w=ancho(t,f,trk); x=(W-w)/2
    if brillo:
        g=Image.new('RGBA',(W,H)); letras(ImageDraw.Draw(g),x,y,t,f,(229,48,74,150),trk); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(28)))
    if sombra:
        s=Image.new('RGBA',(W,H)); letras(ImageDraw.Draw(s),x,y+6,t,f,(0,0,0,210),trk); c.alpha_composite(s.filter(ImageFilter.GaussianBlur(14)))
    letras(ImageDraw.Draw(c),x,y,t,f,col,trk)
txt('Los mejores',505,ImageFont.truetype(BL,84),BLANCO)
tam=200
while ancho('ESTUDIAN',ImageFont.truetype(BL,tam),0.04)>W*0.86: tam-=4
txt('ESTUDIAN',595,ImageFont.truetype(BL,tam),ROJO,brillo=True,trk=0.04)
txt('antes de sentarse a la mesa',1575,ImageFont.truetype(BO,50),BLANCO)
fl=ImageFont.truetype(BL,70); d=ImageDraw.Draw(c); w1=d.textlength('R',font=fl); w2=d.textlength('ÍO',font=fl); x=(W-w1-w2)/2; yl=1700
s=Image.new('RGBA',(W,H)); ImageDraw.Draw(s).text((x,yl+6),'RÍO',font=fl,fill=(0,0,0,200)); c.alpha_composite(s.filter(ImageFilter.GaussianBlur(12)))
d=ImageDraw.Draw(c); d.text((x,yl),'R',font=fl,fill=BLANCO); d.text((x+w1,yl),'ÍO',font=fl,fill=ROJO)
txt('ESTRATEGIA DE PÓKER',1790,ImageFont.truetype(BO,30),(205,205,210),sombra=False,trk=0.18)
c.convert('RGB').save(sys.argv[2],quality=94)
