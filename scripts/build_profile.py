"""Render profile assets using project facts and real public GitHub contributions."""
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import urllib.request
import argparse
import time
import math

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
BG, PANEL, LINE = '#09245A', '#123C83', '#4169AF'
WHITE, MUTED, ACCENT, GOLD = '#FFF9EE', '#C4D8FF', '#FF737B', '#FFD45B'
RED, BLUE, INK = '#E62429', '#1559B7', '#030D25'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'ammarcho-profile'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                return response.read().decode('utf-8')
        except (OSError, TimeoutError):
            if attempt == 2: raise
            time.sleep(2)


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days, self.tips, self.tip = {}, {}, None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-date' in attrs:
            self.days[attrs['id']] = {'date': attrs['data-date'], 'level': int(attrs.get('data-level', 0))}
        if tag == 'tool-tip':
            self.tip = attrs.get('for')

    def handle_data(self, data):
        if self.tip:
            self.tips[self.tip] = self.tips.get(self.tip, '') + data

    def handle_endtag(self, tag):
        if tag == 'tool-tip': self.tip = None


def text(x, y, value, size=20, color=MUTED, weight=400, mono=False):
    font = 'Consolas, monospace' if mono else 'Segoe UI, Arial, sans-serif'
    ribbon = ''
    if mono and weight==600:
        width=len(str(value))*size*.62+18
        ribbon=f'<path d="M{x-8} {y-size-4}H{x+width}L{x+width-8} {y+7}H{x-8}Z" fill="{RED}" stroke="{INK}" stroke-width="1.5"/>'
        color=WHITE
    return ribbon+f'<text x="{x}" y="{y}" fill="{color}" font-family="{font}" font-size="{size}" font-weight="{weight}">{escape(str(value))}</text>'


def rect(x, y, w, h, fill=PANEL, radius=12, stroke=None):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"' + (f' stroke="{stroke}"' if stroke else '') + '/>'


def line(x1, y1, x2, y2, color=LINE):
    return f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}"/>'


def paragraphs(x, y, value, limit, size=20, leading=29, color=MUTED):
    rows, current = [], ''
    for word in value.split():
        if current and len(current) + len(word) + 1 > limit:
            rows.append(current)
            current = word
        else: current = (current + ' ' + word).strip()
    if current: rows.append(current)
    return ''.join(text(x, y+i*leading, row, size, color) for i,row in enumerate(rows)), y+len(rows)*leading


def save(name, w, h, content, label):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label, quote=True)}">'
    svg += '<defs><pattern id="dots" width="13" height="13" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="1.6" fill="#FFF9EE" opacity=".09"/></pattern><clipPath id="frame">'+rect(3,3,w-6,h-6,BG,9)+'</clipPath></defs>'
    svg += rect(2,2,w-4,h-4,INK,11,INK)
    svg += '<g clip-path="url(#frame)">'
    svg += rect(5,5,w-10,h-10,BG,7)
    svg += f'<path d="M{w*.53} 0H{w}V{h}H{w*.83}Z" fill="{BLUE}" opacity=".22"/>'
    svg += rect(w*.57,0,w*.43,h,'url(#dots)',0)
    svg += f'<path d="M0 0H{w}V7H7V{h}H0Z" fill="{RED}"/>'
    if 'applied-ai-lab' not in name:
        svg += web(w+12,-14,120,.18)
    svg += content + '</g>'
    svg += rect(2,2,w-4,h-4,'none',11,'#477BC9') + '</svg>\n'
    (ASSETS / f'{name}.svg').write_text(svg, encoding='utf-8')


def web(cx,cy,radius,opacity=.35):
    c=f'<g fill="none" stroke="{WHITE}" stroke-width="1.3" opacity="{opacity}">'
    for angle in range(0,360,30):
        a=math.radians(angle)
        c+=line(cx,cy,round(cx+radius*math.cos(a),2),round(cy+radius*math.sin(a),2),WHITE)
    for radius in range(23,int(radius)+1,23):
        points=[]
        for angle in range(0,361,30):
            a=math.radians(angle)
            points.append((cx+radius*math.cos(a),cy+radius*math.sin(a)))
        d=f'M{points[0][0]:.2f} {points[0][1]:.2f}'
        for (x1,y1),(x2,y2) in zip(points,points[1:]):
            mx,my=(x1+x2)/2,(y1+y2)/2
            mx,my=cx+(mx-cx)*.94,cy+(my-cy)*.94
            d+=f' Q{mx:.2f} {my:.2f} {x2:.2f} {y2:.2f}'
        c+=f'<path d="{d}"/>'
    return c+'</g>'


def mask(cx,cy,scale=1):
    c=f'<g transform="translate({cx} {cy}) scale({scale})">'
    c+='<path d="M0-111C-73-111-91-57-80 9C-73 63-31 106 0 123C31 106 73 63 80 9C91-57 73-111 0-111Z" fill="#E62429" stroke="#030D25" stroke-width="5"/>'
    c+='<defs><clipPath id="mask-clip"><path d="M0-111C-73-111-91-57-80 9C-73 63-31 106 0 123C31 106 73 63 80 9C91-57 73-111 0-111Z"/></clipPath></defs>'
    c+='<g clip-path="url(#mask-clip)">'+web(0,4,180,.55).replace(WHITE,INK)+'</g>'
    c+='<path d="M-69-36Q-46-30-12 0Q-24 45-54 34Q-72 24-69-36Z" fill="#FFF9EE" stroke="#030D25" stroke-width="8" stroke-linejoin="round"/>'
    c+='<path d="M69-36Q46-30 12 0Q24 45 54 34Q72 24 69-36Z" fill="#FFF9EE" stroke="#030D25" stroke-width="8" stroke-linejoin="round"/>'
    return c+'</g>'


PROJECTS = [
    ('panen-cerdas','01','PanenCerdas','PREDICTIVE AGRICULTURE',
     'Harvest timing, yield and risk prediction from climate and satellite vegetation data.',
     'ML services, Random Forest models, feedback-driven retraining and rollback.',
     'Python / FastAPI / Random Forest / NASA POWER','1st place · UNITY #14','PUBLIC REPOSITORY'),
    ('prakira','02','PRAKIRA','CLIMATE & HEALTH',
     'Climate-sensitive disease early warning across 16 districts in Semarang.',
     'ML forecasting, time-series ensembles, backtesting and weather scenario simulation.',
     'Python / FastAPI / XGBoost / Scikit-learn','3rd place · ANFORCOM DSDC','PUBLIC REPOSITORY'),
    ('pantas','03','PANTAS','COMPUTER VISION',
     'Produce grading for a horticulture marketplace connecting farmers and food industries.',
     'AI services with YOLOv11 segmentation, OpenCV grading rules and scale calibration.',
     'YOLOv11 / OpenCV / FastAPI / Docker',None,'PRIVATE SOURCE'),
    ('portal-scanning','04','PortalScanning','DETECTION & OCR',
     'License plate recognition and vehicle records from camera, video and image inputs.',
     'Built the full application: plate detection, OCR, interface and owner database.',
     'YOLO / OpenCV / EasyOCR / React / PostgreSQL',None,'PRIVATE SOURCE'),
    ('drawing-extractor','05','Drawing Data Extractor','DOCUMENT AUTOMATION',
     'Turn engineering PDF title blocks into structured drawing data for Excel.',
     'Built the desktop app, image preprocessing, OCR extraction and Excel export.',
     'Electron / React / Python / OpenCV / Tesseract',None,'PRIVATE SOURCE'),
]


def build_project(project, mobile=False):
    slug,number,name,category,desc,role,stack,award,visibility = project
    w,x = (440,24) if mobile else (960,34)
    c = text(x,38,number+' / '+category,12 if mobile else 14,ACCENT,600,True)
    c += text(x,83,name,29 if mobile else 34,WHITE,700)
    if not mobile: c += text(745,38,visibility,12,MUTED,mono=True)
    s,y = paragraphs(x,118 if mobile else 123,desc,42 if mobile else 88,17 if mobile else 21,25 if mobile else 30)
    c += s + text(x,y+15,'MY CONTRIBUTION',12,ACCENT,600,True)
    s,y = paragraphs(x,y+43,role,42 if mobile else 91,17 if mobile else 20,25 if mobile else 29)
    c += s + line(x,y+3,w-x,y+3)
    s,y = paragraphs(x,y+32,stack,44 if mobile else 100,14 if mobile else 17,22)
    c += s
    if award:
        c += text(x,y+15,award,15 if mobile else 18,GOLD,600)
        y += 31
    if mobile:
        c += text(x,y+12,visibility,11,MUTED,mono=True)
        y += 26
    save(slug+('-mobile' if mobile else ''),w,y+26,c,name+'. '+desc+' My contribution: '+role)


def build_hero(mobile=False):
    w,h,x = (440,490,24) if mobile else (960,390,34)
    c = f'<path d="M{280 if mobile else 645} 0H{w}V{h}H{380 if mobile else 745}Z" fill="{RED}"/>'
    c += web(w-15,0,280,.35)
    c += text(x,39,'AMMARCHO / THE AMAZING BUILDER',12 if mobile else 14,WHITE,600,True)
    c += text(x+3,124 if mobile else 139,"Hi, I'm Ammar.",44 if mobile else 67,INK,700)
    c += text(x,120 if mobile else 135,"Hi, I'm Ammar.",44 if mobile else 67,WHITE,700)
    s,_ = paragraphs(x,166 if mobile else 186,'Your friendly neighborhood AI builder.',29 if mobile else 44,23 if mobile else 27,32,WHITE)
    c += s
    s,_ = paragraphs(x,252 if mobile else 265,'Applied AI · Computer Vision · ML Systems',32 if mobile else 59,17 if mobile else 20,27,MUTED)
    c += s
    if mobile:
        c += text(x,340,'BUILD.',25,WHITE,700)+text(x,374,'LEARN.',25,WHITE,700)+text(x,408,'REPEAT.',25,GOLD,700)
        c += mask(330,357,.66)
    else:
        c += mask(795,194,1.1)
        c += text(712,355,'BUILD / LEARN / REPEAT',13,WHITE,600,True)
    c += text(x,461 if mobile else 351,'INFORMATION TECHNOLOGY / UGM',12,MUTED,mono=True)
    save('applied-ai-lab'+('-mobile' if mobile else ''),w,h,c,'Ammar. Classic Spider-Man red and blue. Your friendly neighborhood AI builder.')


def build_about(mobile=False):
    w,x = (440,24) if mobile else (960,34)
    c = text(x,37,'01 / THE BUILDER',13,ACCENT,600,True)
    value = "I'm Muhammad Choirudin Ammar, an Information Technology student at Universitas Gadjah Mada. I build AI services, vision pipelines and applications that solve practical problems."
    s,y = paragraphs(x,76,value,43 if mobile else 88,17 if mobile else 21,26 if mobile else 32,WHITE)
    c += s + line(x,y+2,w-x,y+2) + text(x,y+33,'EXPLORING NOW',12,ACCENT,600,True)
    s,y = paragraphs(x,y+62,'Deep learning / YOLO / OpenCV / AI agents',41 if mobile else 90,17 if mobile else 21,26)
    save('about'+('-mobile' if mobile else ''),w,y+20,c+s,'About Ammar. '+value+' Exploring deep learning, YOLO, OpenCV and AI agents.')


def build_stack(mobile=False):
    w,x = (440,24) if mobile else (960,34)
    c = text(x,38,'03 / TOOLKIT',13,ACCENT,600,True)
    groups = [('AI & VISION','Python / YOLO / OpenCV / Scikit-learn / XGBoost / Pandas / NumPy'),('SERVICES & DATA','FastAPI / PostgreSQL / Supabase / SQLAlchemy / Docker'),('WEB & DESKTOP','TypeScript / React / Next.js / Node.js / Electron / Tailwind CSS')]
    y = 80
    for title,tools in groups:
        c += text(x,y,title,13,ACCENT,600,True)
        s,y = paragraphs(x,y+31,tools,42 if mobile else 90,17 if mobile else 21,26 if mobile else 30,WHITE)
        c += s + line(x,y+6,w-x,y+6)
        y += 43
    save('toolkit'+('-mobile' if mobile else ''),w,y-12,c,'Toolkit. '+'. '.join(a+': '+b for a,b in groups))


def build_activity(days,repos,mobile=False):
    w,x = (440,24) if mobile else (960,34)
    total = sum(d['count'] for d in days)
    active = sum(d['count']>0 for d in days)
    run=best=0
    for d in days:
        run = run+1 if d['count'] else 0
        best = max(best,run)
    c = text(x,38,'04 / BUILD LOG',13,ACCENT,600,True)
    c += text(x,79,'Every contribution connects.',26 if mobile else 34,WHITE,700)
    c += text(x,110,'Real GitHub activity · past year',15 if mobile else 18,MUTED)
    labels = [('CONTRIBUTIONS',f'{total:,}'),('ACTIVE DAYS',str(active)),('LONGEST STREAK',str(best)+' days')]
    gap = 12 if mobile else 18
    cw = (w-2*x-2*gap)/3
    for i,(label,value) in enumerate(labels):
        xx = x+i*(cw+gap)
        c += rect(xx,135,cw,93,RED if i==0 else BLUE,5,INK)
        c += text(xx+12,171,value,25 if mobile else 34,WHITE,700)
        c += text(xx+12,205,label,9 if mobile else 12,MUTED,mono=True)
    first = date.fromisoformat(days[0]['date'])
    first -= timedelta(days=(first.weekday()+1)%7)
    last = date.fromisoformat(days[-1]['date'])
    if mobile: first = max(first,last-timedelta(days=(last.weekday()+1)%7+25*7))
    cell,step = (10,15) if mobile else (12,16)
    gx,gy = (x if mobile else x+18),282
    palette = ['#173669','#215DB5','#689FEC','#E86B81',RED]
    seen_month = None
    for d in days:
        dt = date.fromisoformat(d['date'])
        if dt<first: continue
        offset = (dt-first).days
        col,row = offset//7,offset%7
        xx,yy = gx+col*step,gy+row*step
        if row==0 and dt.day<=7 and dt.month!=seen_month:
            c += text(xx,gy-14,dt.strftime('%b'),10 if mobile else 12,MUTED,mono=True)
            seen_month = dt.month
        c += f'<rect x="{xx}" y="{yy}" width="{cell}" height="{cell}" rx="2" fill="{palette[d["level"]]}" stroke="{LINE}" stroke-width=".4"><title>{d["date"]}: {d["count"]} contributions</title></rect>'
    y = gy+7*step+29
    c += text(x,y,'Recent 26 weeks shown · totals cover past year' if mobile else 'Commits, pull requests, issues and other GitHub contributions.',12 if mobile else 15,MUTED)
    c += line(x,y+20,w-x,y+20)
    c += text(x,y+49,f'{repos} public repositories · updated {datetime.now(timezone.utc).strftime("%Y-%m-%d")} UTC',12 if mobile else 15,MUTED,mono=True)
    save('activity'+('-mobile' if mobile else ''),w,y+74,c,f'GitHub activity over the past year: {total} contributions, {active} active days, longest streak {best} days. {repos} public repositories. Contributions include more than commits.')
    return {'contributions':total,'active_days':active,'longest_streak':best,'public_repositories':repos}


def build_footer(mobile=False):
    w,x = (440,24) if mobile else (960,34)
    c = text(x,37,'05 / CONNECT',13,ACCENT,600,True)
    c += text(x,83,"Let's build something amazing.",24 if mobile else 36,WHITE,700)
    c += text(x,121,'Applied AI / Computer vision / Practical tools',15 if mobile else 20,MUTED)
    c += line(x,145,w-x,145,ACCENT) + text(x,179,'GITHUB / AMMARCHO',13 if mobile else 17,ACCENT,600,True)
    save('connect'+('-mobile' if mobile else ''),w,204,c,'Connect with Ammar on GitHub. Applied AI, computer vision and practical tools.')


def build_readme():
    def picture(slug,alt,href=None):
        value = f'<picture>\n  <source media="(max-width: 600px)" srcset="assets/{slug}-mobile.svg" />\n  <img src="assets/{slug}.svg" width="100%" alt="{escape(alt,quote=True)}" />\n</picture>'
        return f'<a href="{href}">\n{value}\n</a>' if href else value
    parts = [picture('applied-ai-lab',"Hi, I'm Ammar. Your friendly neighborhood AI builder. Classic Spider-Man red and blue. Information Technology at UGM."),
        '<p align="center"><a href="#selected-work">Selected work</a> &nbsp; / &nbsp; <a href="#toolkit">Toolkit</a> &nbsp; / &nbsp; <a href="#build-log">Build log</a> &nbsp; / &nbsp; <a href="https://www.instagram.com/xyammar/">Connect ↗</a></p>',
        picture('about','Muhammad Choirudin Ammar. Information Technology student at UGM building AI services, vision pipelines and practical applications. Exploring deep learning, YOLO, OpenCV and AI agents.'),
        '<a id="selected-work"></a>',picture('selected-work','02 / Selected work. AI services, vision pipelines and practical applications.')]
    for project in PROJECTS:
        slug,number,name,category,desc,role,stack,award,visibility = project
        href = 'https://github.com/astrorehan/'+slug if slug in ['panen-cerdas','prakira'] else None
        alt = name+'. '+desc+' My contribution: '+role+' '+stack+'. '+((award+'. ') if award else '')+visibility+'.'
        parts.append(picture(slug,alt,href))
    parts += ['<a id="toolkit"></a>',picture('toolkit','AI and vision: Python, YOLO, OpenCV, Scikit-learn, XGBoost, Pandas, NumPy. Services and data: FastAPI, PostgreSQL, Supabase, SQLAlchemy, Docker. Web and desktop: TypeScript, React, Next.js, Node.js, Electron, Tailwind CSS.'),
        '<a id="build-log"></a>',picture('activity','Real GitHub contributions over the past year, active days, longest streak and public repository count. Updated daily. Contributions include more than commits. Open native GitHub activity.','https://github.com/ammarcho?tab=overview'),
        picture('connect',"Let's build something useful. Explore Ammar's repositories.",'https://github.com/ammarcho?tab=repositories')]
    (ROOT/'README.md').write_text('\n\n'.join(parts)+'\n',encoding='utf-8')


def main():
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--calendar-file',type=Path)
    arguments.add_argument('--user-file',type=Path)
    args = arguments.parse_args()
    ASSETS.mkdir(exist_ok=True)
    parser = CalendarParser()
    calendar = args.calendar_file.read_text(encoding='utf-8') if args.calendar_file else fetch('https://github.com/users/ammarcho/contributions')
    parser.feed(calendar)
    days = []
    for ident,entry in parser.days.items():
        tip = parser.tips.get(ident,'')
        match = re.search(r'([\d,]+) contributions? on',tip)
        if not match and not re.search(r'No contributions on',tip):
            raise ValueError('Missing contribution count for '+entry['date'])
        days.append(dict(entry,count=int(match.group(1).replace(',','')) if match else 0))
    days.sort(key=lambda d:d['date'])
    if not 360<=len(days)<=372 or len({d['date'] for d in days})!=len(days):
        raise ValueError('Unexpected GitHub calendar coverage')
    if any((date.fromisoformat(b['date'])-date.fromisoformat(a['date'])).days!=1 for a,b in zip(days,days[1:])):
        raise ValueError('GitHub calendar contains missing days')
    summary = re.search(r'([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year',calendar)
    if summary and sum(d['count'] for d in days)!=int(summary.group(1).replace(',','')):
        raise ValueError('Daily counts disagree with GitHub calendar summary')
    user = json.loads(args.user_file.read_text(encoding='utf-8-sig') if args.user_file else fetch('https://api.github.com/users/ammarcho'))
    for mobile in [False,True]:
        build_hero(mobile)
        build_about(mobile)
        w,x = (440,24) if mobile else (960,34)
        save('selected-work'+('-mobile' if mobile else ''),w,82,text(x,52,'02 / SELECTED WORK',20 if mobile else 26,ACCENT,600,True),'02 / Selected work')
        for project in PROJECTS: build_project(project,mobile)
        build_stack(mobile)
        stats = build_activity(days,user['public_repos'],mobile)
        build_footer(mobile)
    build_readme()
    print(json.dumps({'calendar_start':days[0]['date'],'calendar_end':days[-1]['date'],'days':len(days),**stats}))


if __name__=='__main__': main()
