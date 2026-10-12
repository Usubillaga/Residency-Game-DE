"""Original, deterministic vector anatomy for the TNM teaching viewer.

The drawings show schematic relationships, never diagnostic imaging or scale.
Tumour extent is a separate overlay so the decisive boundary stays visible.
"""
import html
import math


def L(de, en, es):
    return dict(de=de, en=en, es=es)


INK = '#493d4d'
TUMOUR = '#bd3049'
CORAL = '#e86c80'
URINE = '#e9b64d'
ARTERY = '#d4515d'
VEIN = '#4d86b8'


def path(d, fill='none', stroke=INK, width=2, **attrs):
    return tag('path', d=d, fill=fill, stroke=stroke, **{'stroke-width': width}, **attrs)


def tag(name, **attrs):
    fields = ' '.join(f'{key.replace("_", "-")}="{html.escape(str(value), quote=True)}"' for key, value in attrs.items())
    return f'<{name} {fields}/>'


def ellipse(x, y, rx, ry, fill, stroke=INK, width=2, **attrs):
    return tag('ellipse', cx=x, cy=y, rx=rx, ry=ry, fill=fill, stroke=stroke, **{'stroke-width': width}, **attrs)


def rect(x, y, w, h, fill, rx=8, stroke=INK, width=2, **attrs):
    return tag('rect', x=x, y=y, width=w, height=h, rx=rx, fill=fill, stroke=stroke, **{'stroke-width': width}, **attrs)


def text(x, y, value, size=19, fill=INK, **attrs):
    fields = dict(x=x, y=y, fill=fill, **{'font-size': size, 'font-family': 'sans-serif'}, **attrs)
    start = tag('text', **fields)[:-2] + '>'
    return start + html.escape(str(value)) + '</text>'


def group(part, content):
    return '<g data-part="' + part + '">' + content + '</g>'


def defs():
    colours = {
        'cortex': ('#f6d3cf', '#c9828d'), 'medulla': ('#eaa4a2', '#b77787'),
        'fat': ('#fff5cc', '#e6cf86'), 'vein': ('#a9d5ee', '#477fba'),
        'artery': ('#f3a19d', '#c24e59'), 'tumour': ('#ee8594', '#aa2541'),
        'muscle': ('#f1c0b7', '#ba7786'), 'prostate': ('#debdb7', '#a6788c'),
        'bladder': ('#eec6bf', '#c29199'), 'testis': ('#f4d8c4', '#d1a198'),
        'adrenal': ('#f8dfa3', '#bd9960'), 'skin': ('#f6e7d7', '#d7b6ae'),
    }
    return '<defs>' + ''.join(
        '<linearGradient id="' + key + '" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="' + a + '"/><stop offset="1" stop-color="' + b + '"/>'
        '</linearGradient>' for key, (a, b) in colours.items()) + '</defs>'


def label(id, x, y, anchor_x, anchor_y, number, side='right'):
    elbow = x - 15 if side == 'right' else x + 168
    line = path(f'M{anchor_x} {anchor_y}L{elbow} {anchor_y}L{elbow} {y-7}L{x-5} {y-7}', stroke='#9a8797', width=1.6)
    dot = ellipse(anchor_x, anchor_y, 3.8, 3.8, '#fcfaf4', '#806a83', 1.4)
    return line + dot + text(x, y, number, 18, **{'data-label': id})


def frame(content):
    return defs() + rect(8, 8, 944, 624, '#fffdf8', 20, '#d8cbbd', 1.5) + content


def lesion(x, y, rx, ry, seed=0):
    pts = []
    for i in range(16):
        a = i * math.tau / 16
        r = 1 + .12 * math.sin(i * 2.3 + seed)
        pts.append((round(x + math.cos(a) * rx * r, 1), round(y + math.sin(a) * ry * r, 1)))
    d = 'M' + 'L'.join(f'{px} {py}' for px, py in pts) + 'Z'
    result = path(d, 'url(#tumour)', '#9a2340', 2)
    for i in range(12):
        a = i * 2.4 + seed
        dx, dy = math.cos(a) * rx * .58, math.sin(a) * ry * .56
        result += ellipse(round(x + dx, 1), round(y + dy, 1), 2.3, 2.8, '#f6b0b2', 'none', 0)
    return result


def ruler(x1, x2, y, value):
    return (path(f'M{x1} {y-9}V{y+9}M{x2} {y-9}V{y+9}M{x1} {y}H{x2}', stroke='#806a83', width=1.8)
            + text((x1+x2)/2, y-14, value, 19, **{'text-anchor': 'middle'}))


def kidney(variant=None):
    # Coronal organ section; the caval panel is a separate schematic vessel relationship.
    s = group('gerota', path('M196 125C144 211 149 450 242 523C329 575 502 528 561 434L563 190C502 86 268 55 196 125Z', '#fff5d8', '#988889', 2.5, **{'stroke-dasharray': '7 5'}))
    fat = ''
    for i in range(24):
        a = i * math.tau / 24
        fat += ellipse(round(359 + math.cos(a)*169, 1), round(323+math.sin(a)*195, 1), 11, 8, '#f0dda4', '#d5bc83', .8)
    s += group('perirenal-fat', fat)
    outer = 'M286 156C193 167 191 387 255 459C292 505 360 506 419 470C453 448 481 407 466 379C450 355 412 353 417 318C422 286 474 267 469 231C461 185 368 133 286 156Z'
    s += group('capsule', path(outer, '#fbf1df', '#745967', 5))
    s += group('kidney', path(outer, 'url(#cortex)', '#ad7281', 2.2))
    pyramids = ''
    centres = [(278,207,345,278),(243,274,352,313),(251,355,349,343),(289,421,359,367),(365,452,385,366),(427,419,398,356),(421,214,387,294)]
    for i,(bx,by,tx,ty) in enumerate(centres):
        dx,dy=tx-bx,ty-by;norm=math.hypot(dx,dy);nx,ny=-dy/norm*21,dx/norm*21
        pyramids += path(f'M{bx+nx:.1f} {by+ny:.1f}Q{bx} {by-10} {bx-nx:.1f} {by-ny:.1f}L{tx} {ty}Z','url(#medulla)','#ad7a88',1)
        for q in [-.5,0,.5]:
            pyramids += path(f'M{bx+nx*q:.1f} {by+ny*q:.1f}L{tx} {ty}',stroke='#d19c9f',width=1)
    s += group('renal-medulla', pyramids)
    s += group('sinus', path('M370 253C333 277 307 332 346 373C372 409 432 377 439 345C439 312 424 270 398 248Z','url(#fat)','#c8ad74',1.3))
    collect = path('M346 278Q349 301 381 309M352 313L382 325M349 343L380 343M359 367L382 356M385 366L392 351M398 356L405 342M387 294L395 313',stroke='#e4ae45',width=8,**{'stroke-linecap':'round'})
    collect += path('M390 309C408 304 437 323 452 338L438 359C417 370 387 360 382 344Z','#f7d780','#cc963a',2)
    collect += path('M444 349Q503 382 491 450Q481 498 500 542',stroke=URINE,width=14,**{'stroke-linecap':'round'})
    collect += path('M444 349Q503 382 491 450Q481 498 500 542',stroke='#ffeab0',width=5)
    s += group('collecting-system',collect)
    vessels=path('M424 320C492 300 570 303 650 302',stroke=VEIN,width=28,**{'stroke-linecap':'round'})+path('M426 317C499 303 574 307 650 305',stroke='#a9d6ef',width=11)
    s+=group('renal-vein',vessels)
    s+=group('renal-artery',path('M430 281C481 270 525 271 565 267',stroke=ARTERY,width=13)+path('M430 281L388 268M430 281L383 308M383 308L353 330',stroke=ARTERY,width=5))
    s+=group('cava',path('M646 76Q624 166 640 243L640 469Q641 514 645 557H677Q681 506 679 467V244Q680 148 674 77Z','url(#vein)','#486d98',2.5)+path('M653 98V548',stroke='#bedceb',width=3))
    s+=group('diaphragm',path('M563 175Q640 145 716 167',stroke='#b99da8',width=13)+path('M563 175Q640 145 716 167',stroke='#dbc5cc',width=4))
    adrenal=path('M279 123Q305 75 343 93Q370 94 394 117L366 133Q326 135 301 143Z','url(#adrenal)','#ae8f64',2)
    adrenal+=path('M300 126Q331 109 367 120',stroke='#dbc18b',width=6)
    s+=group('adrenal',adrenal)
    s+=label('kidney',56,218,228,236,1,'left')+label('renal-medulla',55,346,283,350,2,'left')+label('capsule',56,480,245,443,3,'left')
    s+=label('sinus',743,278,363,325,4)+label('renal-vein',742,338,552,309,5)+label('cava',744,92,667,118,6)
    s+=label('diaphragm',743,172,674,163,7)+label('adrenal',54, 99,323,116,8,'left')
    s+=label('collecting-system',739,465,491,448,9)+label('gerota',735,555,555,433,10)
    s+=label('perirenal-fat',54,557,239,461,11,'left')+label('renal-artery',738,223,550,268,12)
    overlay=''
    if variant in ('t1a','t1b','t2a','t2b'):
        size={'t1a':20,'t1b':28,'t2a':38,'t2b':44}[variant]
        overlay=lesion(270,290,size,size*1.12)+ruler(270-size,270+size,210,{'t1a':'≤4 cm','t1b':'>4–7 cm','t2a':'>7–10 cm','t2b':'>10 cm'}[variant])
    elif variant=='t3a-fat':
        overlay=lesion(260,382,34,41)+path('M232 362Q207 366 201 393L221 416L248 416Z','url(#tumour)','#9a2340',2)+lesion(216,391,13,16)
    elif variant=='t3a-sinus':overlay=lesion(374,334,24,34)
    elif variant=='t3a-collecting':overlay=lesion(367,328,35,32)+lesion(424,339,20,11)
    elif variant=='t3a-vein':overlay=lesion(420,321,29,29)+path('M432 312Q492 303 546 311L546 324Q489 318 432 331Z','url(#tumour)','#9a2340',2)
    elif variant in ('t3b','t3c-height','t3c-wall'):
        top=205 if variant=='t3b' else 103 if variant=='t3c-height' else 236
        overlay=lesion(420,321,29,29)+path(f'M432 312Q502 306 643 311L648 {top}Q660 {top-13} 673 {top}L667 328H432Z','url(#tumour)','#9a2340',2)
        if variant=='t3c-wall':overlay+=lesion(678,269,18,25)
    elif variant=='t4':overlay=lesion(263,202,60,38)+path('M250 167Q229 139 204 119L183 152Q198 181 230 196Z','url(#tumour)','#9a2340',2)
    elif variant=='t4-adrenal':overlay=lesion(333,170,49,33)+path('M307 142L310 119Q335 103 359 123L363 161Z','url(#tumour)','#9a2340',2)
    elif variant=='utuc-t3':overlay=lesion(394,328,40,29)+path('M369 303L335 276L319 302L369 338Z','url(#tumour)','#9a2340',2)
    elif variant=='utuc-t4':overlay=lesion(394,328,35,28)+path('M376 322L195 296L189 339L374 345Z','url(#tumour)','#9a2340',2)
    elif variant=='renal-i':overlay=path('M222 256Q194 288 210 348L225 342Q215 300 237 270Z','#aa5b77','#8d4564',1.5)
    elif variant=='renal-ii':overlay=path('M230 289L259 305L254 310L228 301Z',TUMOUR,TUMOUR,1.4)+text(211,263,'<1 cm',17,TUMOUR)
    elif variant=='renal-iii':overlay=path('M224 291L328 330L320 343L226 306Z',TUMOUR,TUMOUR,1.4)+text(242,270,'>1 cm',17,TUMOUR)
    elif variant=='renal-iv-leak':
        overlay=path('M224 303L390 328L389 343L225 317Z',TUMOUR,TUMOUR,1.4)
        for x,y,r in [(225,334,7),(208,360,8),(213,392,10),(230,414,6)]:overlay+=ellipse(x,y,r,r+3,'#76b8cf','#438ca9',1.2)
        overlay+=path('M382 337L226 345',stroke='#76b8cf',width=4,**{'stroke-dasharray':'6 4'})
    elif variant=='renal-iv-infarct':overlay=path(outer,'#a7b5bc','#667b8a',2,opacity='.8')+rect(480,267,20,18,TUMOUR,4)
    elif variant=='renal-v':
        overlay=path('M290 177L320 291L405 375M217 298L334 327L402 477M334 327L288 459M320 291L446 239',stroke=TUMOUR,width=14)
        for x,y,r in [(530,244,11),(548,276,8),(565,312,11),(573,348,9)]:overlay+=ellipse(x,y,r,r+4,'#b42c48','#922943',1)
    return frame(s+group('finding',overlay))


KIDNEY_LABELS=[
 ('kidney',L('Nierenrinde','Renal cortex','Corteza renal')),
 ('renal-medulla',L('Markpyramiden','Medullary pyramids','Pirámides medulares')),
 ('capsule',L('Nierenkapsel','Renal capsule','Cápsula renal')),
 ('sinus',L('Nierensinusfett','Renal sinus fat','Grasa del seno renal')),
 ('renal-vein',L('Nierenvene','Renal vein','Vena renal')),
 ('cava',L('V. cava inferior','Inferior vena cava','Vena cava inferior')),
 ('diaphragm',L('Zwerchfell','Diaphragm','Diafragma')),
 ('adrenal',L('Nebenniere','Adrenal gland','Suprarrenal')),
 ('collecting-system',L('Nierenbecken / Ureter','Renal pelvis / ureter','Pelvis renal / uréter')),
 ('gerota',L('Gerota-Faszie','Gerota fascia','Fascia de Gerota')),
 ('perirenal-fat',L('Perirenales Fett','Perirenal fat','Grasa perirrenal')),
 ('renal-artery',L('Nierenarterie','Renal artery','Arteria renal')),
]


def bladder(variant=None):
    # Left: coronal wall section. Right: magnified wall depth, not a second organ.
    outer='M210 176C103 161 84 277 112 354C133 421 178 442 212 469L225 552H276L288 469C329 442 371 418 389 354C417 275 395 161 297 177Z'
    middle='M211 194C123 181 108 277 131 348C151 402 193 426 230 454L238 537H265L274 454C315 428 352 401 371 348C397 276 380 182 296 195Z'
    inner='M211 209C140 198 129 282 148 343C171 394 212 420 247 445C282 420 325 392 353 343C375 280 360 198 298 211Z'
    s=group('fat',path('M177 146C74 137 51 282 76 366C102 451 160 497 205 520H300C361 495 409 449 429 363C451 279 425 135 325 147Z','url(#fat)','#d5be8c',1.8)+rect(585,432,260,101,'url(#fat)',4,'#cfb780',1.5))
    muscle=path(outer,'url(#muscle)','#9b697d',2.4)+rect(585,296,260,136,'url(#muscle)',4,'#a87583',1.6)
    for i in range(8):muscle+=path(f'M{592+i*33} 306Q{602+i*33} 355 {592+i*33} 421',stroke='#d69fa6',width=2)
    muscle+=path('M585 364H845',stroke='#a36d80',width=1.6,**{'stroke-dasharray':'5 4'})
    s+=group('muscle',muscle)
    s+=group('lamina',path(middle,'#f6ddb0','#d3b28a',1.7)+rect(585,228,260,68,'#f3ddb9',3,'#d1b393',1.3))
    s+=group('urothelium',path(inner,'#f5fbfc','#6eabb8',3)+rect(585,204,260,24,'#b4d8df',3,'#6696a8',1.5))
    mm=''.join(rect(604+i*44,270,24,4,'#be929b',1,'none',0) for i in range(5))
    s+=group('muscularis-mucosae',mm)+label('muscularis-mucosae',854,304,793,272,6)
    s+=path('M161 384Q250 357 343 384L252 449Z','#d4b7b6','#987482',1.5)
    s+=ellipse(180,384,9,4,'#bd8797','#765866',1.4)+ellipse(321,384,9,4,'#bd8797','#765866',1.4)
    s+=path('M183 169Q150 135 164 103M320 168Q356 135 340 101',stroke=URINE,width=15)
    s+=path('M242 550V585M262 550V585',stroke='#ab8794',width=3)
    s+=path('M385 245L579 204M386 341L579 433',stroke='#c6b8c5',width=1.4,**{'stroke-dasharray':'6 5'})
    s+=label('urothelium',584,169,621,214,1)+label('lamina',856,265,806,261,2)+label('muscle',852,350,805,333,3)+label('fat',854,504,803,482,4)
    s+=label('bladder-neck',56,557,248,517,5,'left')
    finding=''
    if variant=='ta':finding=path('M236 439Q238 402 249 417Q256 391 264 418Q281 404 282 436Z','url(#tumour)','#9a2340',2)+lesion(686,198,23,8)
    elif variant=='tis':finding=path('M195 419Q228 444 252 447L275 431',stroke=TUMOUR,width=7)+rect(646,204,96,9,TUMOUR,2)
    elif variant in ('t1','t2a','t2b','t3a','t3b'):
        depth={'t1':273,'t2a':347,'t2b':410,'t3a':430,'t3b':501}[variant]
        finding=path(f'M663 203Q704 187 735 204L727 {depth-10}Q704 {depth+15} 676 {depth-2}Z','url(#tumour)','#9a2340',2)
        finding+=lesion(335,339,16,27)
        if variant=='t3a':finding+=ellipse(711,454,5,5,TUMOUR,TUMOUR,0)+ellipse(701,460,3,3,TUMOUR,TUMOUR,0)
        if variant=='t3b':finding+=lesion(721,466,37,37)
    elif variant=='t4a':
        s+=group('adjacent-prostate',ellipse(300,528,53,38,'url(#prostate)','#a6788c',2))+text(313,590,'P',18)
        s+=label('adjacent-prostate',548,588,312,530,7)
        finding=lesion(293,420,32,39)+path('M277 443Q280 495 300 531L326 519Q314 479 305 438Z','url(#tumour)','#9a2340',2)+lesion(313,519,29,24)
    elif variant=='t4b':
        s+=label('pelvic-wall',553,575,470,395,7)
        finding=lesion(370,330,35,40)+path('M388 303L457 287L465 361L407 372Z','url(#tumour)','#9a2340',2)+rect(459,248,23,173,'#b58f9c',4)+lesion(470,327,18,44)
    elif variant in ('ep','ip','neck'):
        s=group('peritoneal-space',path('M84 160Q249 62 432 160',stroke='#79a49f',width=3,**{'stroke-dasharray':'7 4'}))+s
        if variant=='ip':finding=path('M223 174L247 208M238 174L250 189',stroke=TUMOUR,width=9)
        elif variant=='ep':finding=path('M373 340L397 366',stroke=TUMOUR,width=9)
        else:finding=path('M227 488L271 516',stroke=TUMOUR,width=9)
        dots=[(243,122),(271,101),(305,134)] if variant=='ip' else [(408,358),(439,394),(420,433)] if variant=='ep' else [(270,545),(294,570),(221,558)]
        for x,y in dots:finding+=ellipse(x,y,9,13,'#72aebc','#43899b',1.2)
    return frame(s+group('finding',finding))


BLADDER_LABELS=[('urothelium',L('Urothel / Lumen','Urothelium / lumen','Urotelio / luz')),
 ('lamina',L('Lamina propria','Lamina propria','Lámina propria')),
 ('muscle',L('Muscularis propria','Muscularis propria','Muscular propia')),
 ('fat',L('Perivesikales Fett','Perivesical fat','Grasa perivesical')),
 ('bladder-neck',L('Blasenhals','Bladder neck','Cuello vesical')),('muscularis-mucosae',L('Muscularis mucosae: einzelne Bündel','Muscularis mucosae: small bundles','Muscular de la mucosa: pequeños haces'))]


def prostate(variant=None):
    s=group('rectum',path('M654 115C626 190 669 245 657 316C644 383 675 440 652 516L706 530C735 432 704 389 718 320C728 248 699 194 720 132Z','#d8b3a4','#ab857f',2.2)+path('M680 133C658 206 703 252 682 324C663 389 708 450 681 515',stroke='#f5e4d7',width=23))
    s+=group('bladder',path('M335 140C242 130 211 193 224 258C234 314 289 349 351 350C424 350 474 316 485 265C498 193 459 139 386 141Z','url(#bladder)','#987284',2.2)+path('M338 160C266 156 246 206 255 251C266 298 298 319 353 319C413 320 451 294 456 253C466 196 439 158 385 163Z','#eef7f7','#a699a7',1.5))
    s+=group('seminal',path('M477 280Q510 235 523 265Q548 242 544 279Q571 274 558 302Q590 322 562 334Q578 361 545 356Q549 383 527 371L498 341Z','url(#adrenal)','#ab8a78',2)+path('M510 276Q521 305 541 332L520 355',stroke='#ecd3a7',width=5))
    s+=group('neck',path('M331 320L333 362L382 369L378 320Z','url(#muscle)','#9b758a',2))
    s+=group('extraprostatic',path('M259 381Q313 331 389 361Q478 388 473 477L402 520L280 497Z','url(#fat)','#ddc99a',1.4))
    organ='M315 363C267 373 264 429 293 466C321 503 387 516 424 480C458 446 456 396 416 377C390 363 359 355 315 363Z'
    s+=group('capsule',path(organ,'#fdf2df','#795b6f',5))
    s+=group('prostate',path(organ,'url(#prostate)','#a87687',2.2)+path('M334 387Q298 405 327 466Q350 481 368 470Q393 434 381 392Z','#ca969f','#b77e8b',1.5)+path('M395 387Q433 416 405 472',stroke='#deb4b7',width=5))
    s+=path('M354 320Q353 346 352 362M360 472Q364 504 368 556',stroke='#608b9e',width=12)+path('M354 320Q353 346 352 362M360 472Q364 504 368 556',stroke='#b1d3de',width=5)
    s+=group('urethra',path('M352 362Q348 405 360 472',stroke='#608b9e',width=12)+path('M352 362Q348 405 360 472',stroke='#b1d3de',width=5))
    s+=group('external-sphincter',ellipse(365,519,27,19,'#be8ea2','#8d627d',2)+path('M365 505V533',stroke='#bbd7df',width=6))
    s+=label('extraprostatic',55,487,280,486,8,'left')+label('external-sphincter',740,568,380,522,9)
    s+=path('M474 378Q506 434 489 486',stroke='#eee4cc',width=12)+path('M518 353Q487 355 370 426',stroke='#b6987e',width=3)
    s+=label('bladder',60,194,274,204,1,'left')+label('neck',58,321,346,335,2,'left')+label('prostate',60,428,310,415,3,'left')
    s+=label('urethra',61,557,353,419,4,'left')+label('seminal',741,282,542,304,5)+label('rectum',743,415,702,415,6)+label('capsule',737,511,428,478,7)
    finding=''
    if variant in ('ct1c','ct2a','ct2b','ct2c','pt2'):
        finding=lesion(400,431,13 if variant=='ct2a' else 24,18 if variant=='ct2a' else 34)
        if variant in ('ct2c','pt2'):finding+=lesion(308,432,17,24)
    elif variant=='t3a':finding=lesion(421,445,29,36)+path('M444 434L474 445L460 472L436 463Z','url(#tumour)','#9a2340',2)
    elif variant=='t3a-neck':finding=lesion(359,366,18,18)+ellipse(350,335,4,4,TUMOUR,TUMOUR,0)+ellipse(362,340,4,4,TUMOUR,TUMOUR,0)
    elif variant=='t3b':finding=lesion(415,412,30,28)+path('M413 391Q458 345 516 313L529 335Q474 369 440 416Z','url(#tumour)','#9a2340',2)+lesion(544,320,22,33)
    elif variant=='t4':finding=lesion(429,430,34,34)+path('M452 409L654 404L667 450L459 454Z','url(#tumour)','#9a2340',2)+lesion(657,425,25,46)
    elif variant in ('tis-pu','tis-pd','urethral-t1','urethral-t2'):
        finding=path('M354 374Q352 414 357 447',stroke=TUMOUR,width=7)
        if variant=='tis-pd':finding+=path('M356 421L379 408M378 408L397 395M378 408L397 415',stroke=TUMOUR,width=5)
        if variant=='urethral-t1':finding+=lesion(354,420,12,24)
        if variant=='urethral-t2':finding+=lesion(379,428,29,37)
    return frame(s+group('finding',finding))


PROSTATE_LABELS=[('bladder',L('Blase','Bladder','Vejiga')),('neck',L('Blasenhals','Bladder neck','Cuello vesical')),
 ('prostate',L('Prostata / Stroma','Prostate / stroma','Próstata / estroma')),('urethra',L('Prostatische Urethra','Prostatic urethra','Uretra prostática')),
 ('seminal',L('Samenblase','Seminal vesicle','Vesícula seminal')),('rectum',L('Rektum','Rectum','Recto')),
 ('capsule',L('Prostatagrenze','Prostate boundary','Límite prostático')),('extraprostatic',L('Extraprostatisches Fett','Extraprostatic fat','Grasa extraprostática')),
 ('external-sphincter',L('Äußerer Sphinkter','External sphincter','Esfínter externo'))]


def testis(variant=None):
    s=group('cord',path('M385 68Q399 132 393 183L453 202Q476 134 451 72Z','url(#fat)','#b09b86',2)+path('M407 87Q424 140 414 192',stroke=ARTERY,width=7)+path('M428 87Q444 135 437 194',stroke=VEIN,width=9)+path('M448 96Q466 165 441 216',stroke='#bd9375',width=9))
    skin='M356 170C254 196 233 315 263 435C287 532 404 555 496 506C569 465 583 354 550 267C533 216 487 175 441 177Z'
    s+=group('scrotum',path(skin,'url(#skin)','#a38887',2.2)+path('M286 292Q249 395 306 486M509 234Q560 359 518 456',stroke='#ead0c3',width=5))
    s+=group('vaginalis',path('M369 211C292 223 270 318 292 420C311 498 409 527 482 479C536 445 551 351 522 283C502 230 454 199 406 208Z','#f4eeee','#bd9fa5',2.4))
    s+=group('albuginea',path('M371 228C309 244 288 333 311 419C332 482 407 500 467 462C517 430 531 356 505 294C480 245 424 216 371 228Z','#fcf5e8','#82697c',4))
    s+=group('testis',path('M373 238C318 253 303 334 321 414C340 468 404 483 460 453C505 423 516 361 495 301C473 257 421 229 373 238Z','url(#testis)','#c3989d',1.8))
    tubules=''
    for i in range(15):
        y=273+i*11
        x=350+math.sin(i*.54)*12
        tubules+=path(f'M{x} {y}q-9 7 0 15q17 -18 28 -2q11 17 23 -2q12 -17 26 1q9 11 18 0',stroke='#e8c8b4',width=2.3)
    s+=group('seminiferous-tubules',tubules)
    epid=path('M430 211Q464 179 500 211Q522 226 511 249Q537 274 520 299Q546 329 527 356Q549 389 526 413Q536 442 502 462Q485 481 454 486L450 464Q492 457 498 427Q515 399 497 375Q516 345 499 316Q513 284 491 266Q494 234 463 235Z','url(#adrenal)','#aa8a79',2)
    s+=group('epididymis',epid)
    s+=label('seminiferous-tubules',58,247,436,392,7,'left')
    s+=path('M415 265L476 262M435 264L430 236',stroke='#b49493',width=3)
    s+=label('cord',59,112,426,117,1,'left')+label('testis',58,346,367,351,2,'left')+label('albuginea',53,463,331,450,3,'left')
    s+=label('vaginalis',702,436,414,500,4)+label('epididymis',704,260,498,245,5)+label('scrotum',702,533,480,513,6)
    finding=''
    if variant=='t1':finding=lesion(367,344,40,52)
    elif variant=='t2-vaginalis':finding=lesion(322,370,42,47)+path('M305 348L284 357L290 389L316 405Z','url(#tumour)','#9a2340',2)
    elif variant=='t2-lvi':
        finding=lesion(367,344,36,46)+ellipse(425,302,28,12,'#f2dad1',ARTERY,3)+ellipse(425,302,6,5,TUMOUR,TUMOUR,1)
        finding+=rect(642,72,252,114,'#fff8f4',12,'#c9abb5',1.5)+ellipse(765,128,93,29,'#f4dedc',ARTERY,4)
        for x,y in [(722,122),(756,135),(788,119)]:finding+=ellipse(x,y,7,8,TUMOUR,'#8c2740',1)
        finding+=path('M448 294L657 170',stroke='#be788c',width=1.5,**{'stroke-dasharray':'6 4'})+text(677,167,'LVI',17,TUMOUR)
    elif variant=='t3':finding=lesion(419,272,41,33)+path('M403 252L398 132L439 141L445 256Z','url(#tumour)','#9a2340',2)
    elif variant=='t4':finding=lesion(326,407,45,46)+path('M298 402L258 419L270 470L325 451Z','url(#tumour)','#9a2340',2)
    elif variant in ('testis-iii','testis-iv','testis-v'):
        finding=path('M310 327L415 365L315 400',stroke=TUMOUR,width=10)
        lost='M310 327L410 363L315 400Z' if variant=='testis-iii' else 'M373 238C318 253 303 334 321 414L460 453L405 351Z'
        finding+=path(lost,'#a2758d','#86425f',2,opacity='.85')+text(640,98,'<50%' if variant=='testis-iii' else '>50%' if variant=='testis-iv' else 'V',24,TUMOUR)
        if variant!='testis-iii':finding+=path('M416 251L378 457M486 316L329 412',stroke=TUMOUR,width=11)
        if variant=='testis-v':finding+=path('M350 238L460 453M321 335L501 410',stroke=TUMOUR,width=14)
    return frame(s+group('finding',finding))


TESTIS_LABELS=[('cord',L('Samenstrang','Spermatic cord','Cordón espermático')),('testis',L('Hodenparenchym','Testicular tissue','Parénquima testicular')),
 ('albuginea',L('Tunica albuginea','Tunica albuginea','Túnica albugínea')),('vaginalis',L('Tunica vaginalis','Tunica vaginalis','Túnica vaginal')),
 ('epididymis',L('Nebenhoden','Epididymis','Epidídimo')),('scrotum',L('Skrotalwand','Scrotal wall','Pared escrotal')),
 ('seminiferous-tubules',L('Samenkanälchen','Seminiferous tubules','Túbulos seminíferos'))]


def penis(variant=None):
    s=group('skin',path('M134 189C251 171 373 184 512 177Q576 130 630 177Q693 221 634 271Q583 314 520 280C373 294 243 287 140 293Z','url(#skin)','#b89494',2))
    s+=group('cavernosa',path('M158 198C270 190 399 195 525 194Q547 218 532 239C384 247 266 246 158 239Z','url(#muscle)','#8d6e83',3))
    s+=group('tunica-cavernosa',path('M155 196C267 188 399 192 529 192M155 242C287 251 411 248 533 241',stroke='#7a647d',width=5))
    trabecula=''
    for i in range(20):
        x=166+i*18
        trabecula+=path(f'M{x} 200q9 15 0 37M{x} 213l17 -8M{x} 226l16 8',stroke='#d49daa',width=1.3)
    s+=group('erectile-tissue',trabecula)
    s+=group('spongiosum',path('M157 252C275 253 403 257 522 250Q551 207 588 179Q638 181 643 224Q640 269 586 284Q552 287 528 273L158 280Z','url(#prostate)','#986d83',2))
    s+=group('urethra',path('M159 265C273 266 407 267 539 265L628 236',stroke='#70a1b3',width=10)+path('M159 265C273 266 407 267 539 265L628 236',stroke='#d6ebee',width=3))
    s+=group('glans',path('M533 250Q551 207 588 179Q638 181 643 224Q640 269 586 284Q552 287 528 273','none','#b27b85',2))+path('M533 250Q551 207 588 179Q638 181 643 224Q640 269 586 284Q552 287 528 273',stroke='#ead6b5',width=8)
    # Axial inset: paired dorsal cavernosa, ventral spongiosum and urethra.
    s+=ellipse(729,431,115,108,'url(#skin)','#bd9698',2)
    s+=ellipse(685,396,40,45,'url(#muscle)','#715f7a',3)+ellipse(772,396,40,45,'url(#muscle)','#715f7a',3)
    s+=ellipse(729,477,43,33,'url(#prostate)','#986d83',2)+ellipse(729,477,13,10,'#def0f0','#739bad',2)
    s+=path('M412 299L619 363M525 177L665 336',stroke='#c5b5c6',width=1.4,**{'stroke-dasharray':'6 4'})
    s+=label('cavernosa',78,98,321,213,1,'left')+label('spongiosum',70,375,332,275,2,'left')
    s+=label('urethra',59,471,473,266,3,'left')+label('glans',703,192,595,213,4)+label('tunica-cavernosa',684,584,773,360,5)
    s+=label('skin',55,326,138,291,6,'left')
    finding=''
    if variant in ('t1a','t1b'):
        finding=lesion(640,224,6,11)
        if variant=='t1b':
            finding+=rect(65,503,405,92,'#fff8f4',10,'#c9abb5',1.5)+ellipse(263,545,135,17,'#f4dedc',ARTERY,3)
            for x,y in [(207,544),(260,548),(310,540)]:finding+=ellipse(x,y,6,7,TUMOUR,'#8c2740',1)
            finding+=text(96,576,'LVI / PNI / G3',18,TUMOUR)
    elif variant=='t2':finding=lesion(572,246,31,28)+lesion(732,470,28,21)
    elif variant=='t3':finding=lesion(487,215,37,24)+lesion(685,396,29,34)
    elif variant=='t4':finding=lesion(185,233,57,40)+path('M144 217L104 175L84 204L136 251Z','url(#tumour)','#9a2340',2)
    elif variant=='fracture':finding=path('M396 192L420 226L397 243',stroke=TUMOUR,width=9)+ellipse(411,173,42,20,'#986086','#784b6d',2)
    return frame(s+group('finding',finding))


PENIS_LABELS=[('cavernosa',L('Corpora cavernosa','Corpora cavernosa','Cuerpos cavernosos')),('spongiosum',L('Corpus spongiosum','Corpus spongiosum','Cuerpo esponjoso')),
 ('urethra',L('Urethra','Urethra','Uretra')),('glans',L('Glans penis','Glans penis','Glande')),
 ('tunica-cavernosa',L('Kavernöse Albuginea','Cavernosal albuginea','Albugínea cavernosa')),('skin',L('Haut / äußere Hülle','Skin / outer covering','Piel / cubierta externa'))]


def ureter(variant=None):
    # Longitudinal continuity on the left; wall-depth inset on the right.
    s=group('adventitia',path('M306 90Q276 247 305 370Q327 467 299 562H365Q393 467 369 370Q340 247 371 90Z','url(#fat)','#cbb68b',2))
    s+=group('ureter-muscle',path('M317 90Q288 244 318 369Q340 467 311 562H352Q379 467 355 368Q325 245 357 90Z','url(#muscle)','#a37587',2)+rect(607,335,229,96,'url(#muscle)',4))
    s+=group('lamina',path('M325 91Q301 245 330 366Q352 467 323 562H341Q364 467 345 366Q316 245 347 91Z','#f2dfb8','#c4a894',1.5)+rect(607,264,229,71,'#f2dfb8',4))
    s+=group('urothelium',path('M335 92Q310 245 338 365Q360 467 331 562',stroke='#78a8b5',width=6)+rect(607,242,229,22,'#b4d8df',3))
    s+=group('periureteral-fat',rect(607,431,229,96,'url(#fat)',4,'#cbb68b',1.5))
    s+=path('M339 171L600 242M359 425L600 527',stroke='#bfafbf',width=1.5,**{'stroke-dasharray':'6 4'})
    s+=label('adventitia',56,510,367,498,5,'left')
    s+=label('ureter-muscle',58,232,315,230,1,'left')+label('urothelium',856,255,786,252,2)+label('lamina',856,318,786,306,3)+label('periureteral-fat',851,514,787,485,4)
    f=''
    if variant in ('ta','tis','t1','t2','t3'):
        depth={'ta':238,'tis':250,'t1':311,'t2':403,'t3':482}[variant]
        f=lesion(690,depth,25,9) if variant=='ta' else rect(647,242,104,8,TUMOUR,2) if variant=='tis' else path(f'M658 240Q693 231 730 243L727 {depth}Q692 {depth+17} 671 {depth}Z','url(#tumour)','#9a2340',2)
        f+=lesion(339,317,7 if variant in ('ta','tis','t1') else 21,22)
    elif variant in ('i','ii','iii','iv','v'):
        if variant=='i':f=ellipse(300,320,22,40,'#a9788b','#925973',2)
        elif variant in ('ii','iii'):
            cut=326 if variant=='ii' else 349
            f=path(f'M299 315H{cut}V328H299Z',TUMOUR,TUMOUR,1)+text(80,405,'<50%' if variant=='ii' else '>50%',24,TUMOUR)
        else:
            gap=20 if variant=='iv' else 75
            f=rect(281,303,107,gap,'#fffdf8',0,'none',0)+path(f'M300 303H373M304 {303+gap}H375',stroke=TUMOUR,width=6)+ruler(409,409+gap*1.5,326,'<2 cm' if variant=='iv' else '>2 cm')
            f+=path(f'M300 303Q285 {330+gap} 307 {354+gap}',stroke='#839f88',width=12,opacity='.55')
        if variant!='i':
            for x,y in [(259,350),(285,395),(265,434)]:f+=ellipse(x,y,8,11,'#76b8cf','#438ca9',1.2)
    return frame(s+group('finding',f))


URETER_LABELS=[('ureter-muscle',L('Uretermuskulatur','Ureteric muscle','Músculo ureteral')),('urothelium',L('Urothel / Lumen','Urothelium / lumen','Urotelio / luz')),
 ('lamina',L('Subepitheliales Bindegewebe','Subepithelial tissue','Tejido subepitelial')),('periureteral-fat',L('Periureterales Fett','Periureteric fat','Grasa periureteral')),
 ('adventitia',L('Äußere Hülle / Blutversorgung','Outer coat / blood supply','Capa externa / irrigación'))]


def adrenal(variant=None):
    s=group('cava',path('M604 87V554H647V87Z','url(#vein)','#4775a4',2)+path('M614 91V550',stroke='#a8d3ec',width=4))
    s+=group('kidney',path('M390 337C319 333 289 400 308 466C328 524 397 558 454 523C479 505 463 477 442 454C423 431 481 422 465 388C452 358 417 340 390 337Z','url(#cortex)','#a37584',2)+path('M409 380L383 407L419 437L432 478',stroke='#e3ae51',width=9))
    s+=group('periadrenal',path('M263 148Q302 94 383 100Q489 89 525 156L540 296Q471 350 392 308L284 305Z','url(#fat)','#d5bf90',1.8))
    outline='M280 230Q313 129 373 152Q441 91 484 176L509 267Q467 304 414 270Q342 303 280 270Z'
    s+=group('capsule',path(outline,'#fff4df','#826b73',5))
    s+=group('cortex',path(outline,'url(#adrenal)','#bf9d69',2))
    s+=group('medulla',path('M306 246Q326 179 376 194Q426 157 458 198L477 251Q448 272 413 242Q359 273 306 255Z','#c39898','#a47684',1.8))
    s+=group('adrenal-vein',path('M486 252Q542 249 607 261',stroke=VEIN,width=16))
    s+=group('sympathetic',ellipse(561,369,20,35,'#d5b7a4','#a88782',2)+path('M560 339V302M560 404V462',stroke='#c3a394',width=6))
    s+=label('periadrenal',57,471,513,298,8,'left')
    s+=label('cortex',55,165,323,201,1,'left')+label('medulla',56,292,383,237,2,'left')+label('capsule',57,381,280,263,3,'left')
    s+=label('cava',745,124,635,135,4)+label('adrenal-vein',744,248,561,256,5)+label('kidney',740,504,437,505,6)+label('sympathetic',740,397,568,370,7)
    f=''
    if variant in ('acc-t1','acc-t2','ppgl-t1','ppgl-t2'):
        small=variant.endswith('t1');f=lesion(382,224,25 if small else 62,21 if small else 47)+ruler(348 if small else 320,417 if small else 450,330,'≤5 cm' if variant=='acc-t1' else '>5 cm' if variant=='acc-t2' else '<5 cm' if small else '≥5 cm')
    elif variant=='pgl-t2':f=lesion(561,370,22,34)+text(538,479,'PGL',18,TUMOUR)
    elif variant in ('acc-t3','ppgl-t3-fat'):f=lesion(314,245,38,30)+path('M291 228L264 207L253 253L288 262Z','url(#tumour)','#9a2340',2)
    elif variant in ('acc-t4','ppgl-t3'):
        f=lesion(472,242,36,38)+path('M482 250L620 248L620 276L484 274Z','url(#tumour)','#9a2340',2)+lesion(642,262,14,20)
    elif variant=='acc-t4-kidney':f=lesion(409,268,36,34)+path('M389 284L385 371L427 379L431 282Z','url(#tumour)','#9a2340',2)+lesion(407,372,27,29)
    return frame(s+group('finding',f))


ADRENAL_LABELS=[('cortex',L('Nebennierenrinde','Adrenal cortex','Corteza suprarrenal')),('medulla',L('Nebennierenmark','Adrenal medulla','Médula suprarrenal')),
 ('capsule',L('Organkapsel','Organ capsule','Cápsula del órgano')),('cava',L('V. cava inferior','Inferior vena cava','Vena cava inferior')),
 ('adrenal-vein',L('Nebennierenvene','Adrenal vein','Vena suprarrenal')),('kidney',L('Niere','Kidney','Riñón')),
 ('sympathetic',L('Sympathisches Paraganglion','Sympathetic paraganglion','Paraganglio simpático')),('periadrenal',L('Periadrenales Gewebe','Periadrenal tissue','Tejido perisuprarrenal'))]


def urethra(variant=None):
    # Male sagittal route. Numbered landmarks are the clinically decisive segments.
    s=group('bladder',path('M310 123C231 123 220 205 262 244Q298 279 347 255C407 222 412 141 352 125Z','url(#bladder)','#987284',2)+ellipse(317,195,64,55,'#eef7f7','#a699a7',1.3))
    s+=group('pubis',path('M425 246Q416 279 446 317L473 291Q447 270 462 240Z','#eadfd1','#ac9b92',2))
    s+=group('prostate',ellipse(320,288,56,42,'url(#prostate)','#936c82',2))
    s+=group('cavernosa',path('M462 377Q520 418 696 426L736 460L705 486Q534 467 456 420Z','url(#muscle)','#8d6e83',3))
    s+=group('spongiosum',path('M303 381Q349 356 383 388Q422 429 479 440L702 477L746 462L762 486Q735 517 695 507L472 474Q416 464 372 425Q344 419 320 430Z','url(#prostate)','#986d83',2))
    route='M319 245V343Q305 370 326 396Q361 391 388 421Q429 458 479 456L704 493L748 478'
    s+=path(route,stroke='#6b9bad',width=12)+path(route,stroke='#c8e3e7',width=4)
    s+=group('prostatic-urethra',path('M319 245V330',stroke='#6b9bad',width=12)+path('M319 245V330',stroke='#c8e3e7',width=4))
    s+=group('urethra',path('M479 456L704 493L748 478',stroke='#6b9bad',width=12)+path('M479 456L704 493L748 478',stroke='#c8e3e7',width=4))
    s+=group('sphincter',ellipse(319,343,25,13,'#af879b','#7f617c',2)+path('M319 331V355',stroke='#bddce4',width=6))
    s+=label('bladder',52,133,280,171,1,'left')+label('prostatic-urethra',52,269,319,288,2,'left')+label('sphincter',52,347,320,341,3,'left')+label('spongiosum',51,448,342,416,4,'left')
    s+=label('pubis',738,228,443,271,5)+label('cavernosa',741,366,585,428,6)+label('urethra',741,565,621,479,7)
    f=''
    if variant=='anterior':f=ellipse(512,469,31,22,'#976682','#7c4469',2)+path('M504 460L515 480',stroke=TUMOUR,width=7)
    elif variant=='posterior':f=path('M307 338L335 354',stroke=TUMOUR,width=7)+path('M444 247L433 275L459 299',stroke=TUMOUR,width=5)
    elif variant in ('partial','complete'):
        f=rect(291,333,55,22,'#fffdf8',0,'none',0)+path('M311 331V358M330 331V358',stroke='#6598ab',width=6)
        if variant=='partial':f+=path('M311 333L317 354',stroke='#bbdce3',width=6)
        for x,y in [(350,355),(376,342),(389,369)]:f+=ellipse(x,y,7,10,'#76b8cf','#438ca9',1.2)
    elif variant in ('t1','t2','t3','t4'):
        if variant=='t1':f=lesion(608,479,14,8)
        if variant=='t2':f=lesion(589,480,23,17)
        if variant=='t3':f=lesion(566,458,27,35)
        if variant=='t4':f=lesion(314,290,39,41)+path('M300 277L288 204L322 187L330 274Z','url(#tumour)','#9a2340',2)
    return frame(s+group('finding',f))


URETHRA_LABELS=[('bladder',L('Blase','Bladder','Vejiga')),('prostatic-urethra',L('Prostatische Urethra','Prostatic urethra','Uretra prostática')),
 ('sphincter',L('Membranöse Urethra / Sphinkter','Membranous urethra / sphincter','Uretra membranosa / esfínter')),
 ('spongiosum',L('Bulbäre Urethra / Spongiosum','Bulbar urethra / spongiosum','Uretra bulbar / esponjoso')),('pubis',L('Schambein','Pubic bone','Pubis')),
 ('cavernosa',L('Corpus cavernosum','Corpus cavernosum','Cuerpo cavernoso')),('urethra',L('Penile Urethra','Penile urethra','Uretra peneana'))]


def spread(organ, code, site=None):
    # Schematic nodal stations, deliberately not a radiology scan or staging test.
    s=group('body',path('M354 113Q314 123 302 170L265 345L291 359L333 237L327 389L314 562H350L385 411L416 562H452L438 389L431 237L473 357L501 343L464 169Q453 126 412 112Z','#f1e4d7','#cbb8ac',2)+ellipse(384,74,36,43,'#f1e4d7','#cbb8ac',2))
    s+=group('lung',path('M365 159Q338 171 338 223Q347 248 371 235V165Z','#d9b5b8','#b28f9d',1.4)+path('M399 159Q428 171 428 223Q416 248 395 235V165Z','#d9b5b8','#b28f9d',1.4))
    s+=group('liver',path('M335 256Q385 243 433 266L404 292Q364 295 335 277Z','#c69b86','#a97871',1.4))
    s+=group('bone',path('M380 146V394M355 403L333 550M417 403L437 550',stroke='#e3c884',width=9))
    primary_x=345 if organ=='utuc' and site=='distal' else 348 if organ in ('rcc','utuc','acc','ppgl') else 384
    primary_y=343 if organ=='utuc' and site=='distal' else 266 if organ in ('acc','ppgl') else 294 if organ in ('rcc','utuc') else 405 if organ in ('testis','penile') or site=='anterior' else 370
    s+=group('primary',ellipse(primary_x,primary_y,11,14,'#a89cbb','#807091',1.8))
    s+=group('distant-nodes',ellipse(426,130,7,6,'#b8c7aa','#8aa180',1.3))
    region='pelvic' if organ=='utuc' and site=='distal' else 'groin' if organ=='urethral' and site=='anterior' else 'retro' if organ in ('rcc','utuc','testis','acc','ppgl') else 'groin' if organ=='penile' else 'pelvic'
    pts=[(367,289),(403,288),(365,310),(403,309)] if region=='retro' else [(345,382),(424,382),(344,397),(426,397)] if region=='groin' else [(365,352),(403,352),(367,371),(402,371)]
    s+=group('regional-nodes',''.join(ellipse(x,y,7,5,'#b8c7aa','#8aa180',1.3) for x,y in pts))
    if region=='groin':
        s+=group('pelvic-nodes',''.join(ellipse(x,y,6,5,'#b8c7aa','#8aa180',1.3) for x,y in [(365,352),(403,352)]))+label('pelvic-nodes',55,492,365,352,8,'left')
    s+=group('common-iliac',''.join(ellipse(x,y,6,5,'#b8c7aa','#8aa180',1.3) for x,y in [(365,332),(403,332)]))
    s+=label('common-iliac',736,423,403,332,7)
    s+=label('primary',55,415,primary_x,primary_y,1,'left')
    s+=label('regional-nodes',737,335,*pts[0],2)+label('distant-nodes',739,129,426,130,3)+label('lung',740,198,416,194,4)+label('liver',740,277,406,267,5)+label('bone',740,497,435,503,6)
    f=''
    if 'N' in code and not code.endswith('0'):
        n=1 if code.endswith('1') else 3
        for x,y in pts[:n]:f+=ellipse(x,y,8,6,TUMOUR,'#922c44',1)
        f+=rect(50,65,232,75,'#fff8f4',10,'#c9abb5',1.5)+ellipse(163,99,34,22,'#b5c6a9','#738969',3)+lesion(163,99,23,14)
        if code.endswith('3') and organ in ('bladder','penile'):
            for x,y in ([(365,332),(403,332)] if organ=='bladder' else [(365,352),(403,352)]):f+=ellipse(x,y,8,6,TUMOUR,'#922c44',1)
        if (code=='pN2' and organ=='testis') or (code=='pN3' and organ=='penile'):f+=path('M194 92L211 92L210 108L191 105Z',TUMOUR,'#922c44',1)
        f+=text(123,162,code,22,TUMOUR)
    elif code.startswith('M') and code!='M0':
        if organ=='ppgl':targets=[(435,502)] if code=='M1a' else [(402,273),(416,199)] if code=='M1b' else [(435,502),(402,273)]
        elif organ=='prostate':targets=[(426,130)] if code=='M1a' else [(435,502)] if code=='M1b' else [(402,273)]
        elif organ=='testis':targets=[(416,199),(426,130)] if code=='M1a' else [(402,273)]
        elif organ=='bladder':targets=[(426,130)] if code=='M1a' else [(402,273)]
        else:targets=[(416,199),(402,273)]
        for x,y in targets:f+=lesion(x,y,10,10)
        for x,y in targets:f+=path(f'M384 365Q540 301 {x} {y}',stroke='#c57989',width=1.7,**{'stroke-dasharray':'6 5'})
    return frame(s+group('finding',f))


SPREAD_LABELS=[('primary',L('Primärtumor: schematische Lage','Primary: schematic location','Primario: ubicación esquemática')),
 ('regional-nodes',L('Regionale Lymphknoten','Regional lymph nodes','Ganglios regionales')),('distant-nodes',L('Nichtregionale Lymphknoten','Nonregional nodes','Ganglios no regionales')),
 ('lung',L('Lunge','Lung','Pulmón')),('liver',L('Leber','Liver','Hígado')),('bone',L('Knochen','Bone','Hueso')),
 ('common-iliac',L('Gemeinsame Iliakalstation','Common iliac station','Estación ilíaca común'))]


def markers(code):
    # Three independent marker axes: the highest fulfilled group decides S.
    s=rect(195,95,571,430,'#faf6ed',12,'#d6c7bd',1.5)
    colours=['#7aa9a3','#e3bc6f','#c86682']
    for j,marker in enumerate(('LDH / ULN','hCG','AFP')):
        x=246+j*165
        s+=text(x+45,135,marker,22,**{'text-anchor':'middle'})
        for i in range(3):s+=rect(x,172+i*101,91,83,colours[i],10,'#8e7684',1.4)
        s+=text(x+45,213,['<1.5','<5,000','<1,000'][j],16,**{'text-anchor':'middle'})
        s+=text(x+45,314,['1.5–10','5,000–50,000','1,000–10,000'][j],14,**{'text-anchor':'middle'})
        s+=text(x+45,415,['>10','>50,000','>10,000'][j],16,**{'text-anchor':'middle'})
    i=int(code[-1])-1
    s+=path(f'M225 {163+i*101}H735V{267+i*101}H225Z',stroke=TUMOUR,width=4)+text(801,225+i*101,code,28,TUMOUR)
    s+=text(480,490,'LDH: × ULN · hCG: IU/L · AFP: ng/mL',18,**{'text-anchor':'middle'})
    return frame(group('finding',s))


def bladder_trauma(variant=None):
    # Simplified sagittal bladder, with peritoneal covering over the dome.
    s=group('intraperitoneal',path('M144 87H814V225Q670 169 580 180Q410 123 243 233L144 268Z','#e8f0e9','#acbcb1',1.4))
    for i in range(5):
        x=230+i*105
        s+=path(f'M{x} 126q-22 -19 -38 5q-10 22 20 29q31 -15 39 6q-4 28 -35 20',stroke='#bfbaa5',width=14,**{'stroke-linecap':'round'})
        s+=path(f'M{x} 126q-22 -19 -38 5q-10 22 20 29q31 -15 39 6q-4 28 -35 20',stroke='#e0d9bc',width=9,**{'stroke-linecap':'round'})
    s+=group('extraperitoneal',path('M161 272Q250 205 379 252Q464 225 605 245L807 247V526H182Z','url(#fat)','#d1bb8c',1.5))
    outer='M386 212C287 215 250 294 282 382Q306 448 378 464L385 527H440L447 464Q554 457 585 382C622 296 548 202 465 214Z'
    s+=group('bladder',path(outer,'url(#muscle)','#9c7486',3)+path('M387 238C309 239 279 302 306 374Q330 424 410 439Q510 432 555 373C582 308 532 233 464 240Z','#eef7f7','#769fab',2))
    # Green line is the peritoneal reflection; the rupture must actually cross it in IP examples.
    s+=path('M167 271Q252 236 287 256Q326 186 386 207Q474 176 554 243L810 244',stroke='#68958b',width=4,**{'stroke-dasharray':'7 4'})
    s+=group('neck',path('M378 464L385 527H440L447 464Q413 473 378 464Z','url(#prostate)','#9c7486',2)+path('M405 478V565M423 478V565',stroke='#74a0af',width=4))
    s+=label('intraperitoneal',50,120,500,123,1,'left')+label('extraperitoneal',55,476,276,454,2,'left')+label('bladder',744,297,550,279,3)+label('neck',735,535,436,497,4)
    f=''
    if variant=='i':f=ellipse(295,350,19,33,'#af8293','#935f79',2)
    elif variant and variant.startswith('ep'):
        large=variant.endswith('large');f=path('M278 328L303 350L280 373' if large else 'M281 342L303 352',stroke=TUMOUR,width=7)+text(620,421,'>2 cm' if large else '<2 cm',20,TUMOUR)
        for x,y in [(252,344),(225,373),(244,407)]:f+=ellipse(x,y,9,12,'#76b8cf','#438ca9',1.2)
    elif variant and variant.startswith('ip'):
        large=variant.endswith('large');f=path('M400 205L419 241L451 210' if large else 'M410 207L424 237',stroke=TUMOUR,width=7)+text(620,421,'>2 cm' if large else '<2 cm',20,TUMOUR)
        for x,y in [(430,174),(397,150),(469,153)]:f+=ellipse(x,y,9,12,'#76b8cf','#438ca9',1.2)
    elif variant=='neck':
        f=path('M378 485L448 506',stroke=TUMOUR,width=8)
        for x,y in [(389,548),(457,532)]:f+=ellipse(x,y,9,12,'#76b8cf','#438ca9',1.2)
    return frame(s+group('finding',f))


BLADDER_TRAUMA_LABELS=[('intraperitoneal',L('Intraperitonealer Raum / Darm','Intraperitoneal space / bowel','Espacio intraperitoneal / intestino')),
 ('extraperitoneal',L('Extraperitonealer Raum','Extraperitoneal space','Espacio extraperitoneal')),
 ('bladder',L('Blasenwand / Kuppel','Bladder wall / dome','Pared vesical / cúpula')),('neck',L('Blasenhals','Bladder neck','Cuello vesical'))]
