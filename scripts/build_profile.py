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

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
BG, PANEL, LINE = '#0D1117', '#111D25', '#263B45'
WHITE, MUTED, TEAL, GOLD = '#E6EDF3', '#A6BAC5', '#2DD4BF', '#FBBF24'


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
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="{font}" font-size="{size}" font-weight="{weight}">{escape(str(value))}</text>'


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
    svg += rect(1,1,w-2,h-2,BG,18,LINE) + content + '</svg>\n'
    (ASSETS / f'{name}.svg').write_text(svg, encoding='utf-8')


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
    c = text(x,38,number+' / '+category,12 if mobile else 14,TEAL,600,True)
    c += text(x,83,name,29 if mobile else 34,WHITE,700)
    if not mobile: c += text(745,38,visibility,12,MUTED,mono=True)
    s,y = paragraphs(x,118 if mobile else 123,desc,42 if mobile else 88,17 if mobile else 21,25 if mobile else 30)
    c += s + text(x,y+15,'MY CONTRIBUTION',12,TEAL,600,True)
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
    w,h,x = (440,350,24) if mobile else (960,350,34)
    c = text(x,39,'AMMARCHO / APPLIED AI LAB',13,TEAL,600,True)
    c += line(x,59,w-x,59,TEAL)
    c += text(x,122,"Hi, I'm Ammar.",44 if mobile else 65,WHITE,700)
    s,_ = paragraphs(x,162 if mobile else 171,'Turning models into useful tools.',30 if mobile else 60,24 if mobile else 28,32,TEAL)
    c += s
    s,_ = paragraphs(x,239 if mobile else 217,'Applied AI · Computer Vision · ML Systems',32 if mobile else 70,17 if mobile else 20,27)
    c += s + text(x,317,'INFORMATION TECHNOLOGY / UGM',12,MUTED,mono=True)
    if not mobile:
        for xx,yy in [(765,104),(866,151),(757,224),(854,268)]:
            c += line(809,184,xx,yy,'#346A70')
            c += f'<circle cx="{xx}" cy="{yy}" r="7" fill="{BG}" stroke="{TEAL}"/>'
        c += rect(780,151,58,68,'#13343A',10,TEAL)
        for yy in [168,181,194]: c += line(792,yy,826,yy,TEAL)
        c += f'<circle cx="827" cy="208" r="3" fill="{GOLD}"/>'
        c += '<path d="M718 131V83H765M858 83H905V131M905 242V290H858M765 290H718V242" stroke="#2DD4BF" stroke-width="2" fill="none"/>'
    save('applied-ai-lab'+('-mobile' if mobile else ''),w,h,c,'Ammar. Applied AI Lab. Turning models into useful tools.')


def build_about(mobile=False):
    w,x = (440,24) if mobile else (960,34)
    c = text(x,37,'01 / THE BUILDER',13,TEAL,600,True)
    value = "I'm Muhammad Choirudin Ammar, an Information Technology student at Universitas Gadjah Mada. I build AI services, vision pipelines and applications that solve practical problems."
    s,y = paragraphs(x,76,value,43 if mobile else 88,17 if mobile else 21,26 if mobile else 32,WHITE)
    c += s + line(x,y+2,w-x,y+2) + text(x,y+33,'EXPLORING NOW',12,TEAL,600,True)
    s,y = paragraphs(x,y+62,'Deep learning / YOLO / OpenCV / AI agents',41 if mobile else 90,17 if mobile else 21,26)
    save('about'+('-mobile' if mobile else ''),w,y+20,c+s,'About Ammar. '+value+' Exploring deep learning, YOLO, OpenCV and AI agents.')


def build_stack(mobile=False):
    w,x = (440,24) if mobile else (960,34)
    c = text(x,38,'03 / TOOLKIT',13,TEAL,600,True)
    groups = [('AI & VISION','Python / YOLO / OpenCV / Scikit-learn / XGBoost / Pandas / NumPy'),('SERVICES & DATA','FastAPI / PostgreSQL / Supabase / SQLAlchemy / Docker'),('WEB & DESKTOP','TypeScript / React / Next.js / Node.js / Electron / Tailwind CSS')]
    y = 80
    for title,tools in groups:
        c += text(x,y,title,13,TEAL,600,True)
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
    c = text(x,38,'04 / BUILD LOG',13,TEAL,600,True)
    c += text(x,79,'Small steps. Visible progress.',26 if mobile else 34,WHITE,700)
    c += text(x,110,'Real GitHub activity · past year',15 if mobile else 18,MUTED)
    labels = [('CONTRIBUTIONS',f'{total:,}'),('ACTIVE DAYS',str(active)),('LONGEST STREAK',str(best)+' days')]
    gap = 12 if mobile else 18
    cw = (w-2*x-2*gap)/3
    for i,(label,value) in enumerate(labels):
        xx = x+i*(cw+gap)
        c += rect(xx,135,cw,93,PANEL,10,LINE)
        c += text(xx+12,171,value,25 if mobile else 34,TEAL,700)
        c += text(xx+12,205,label,9 if mobile else 12,MUTED,mono=True)
    first = date.fromisoformat(days[0]['date'])
    first -= timedelta(days=(first.weekday()+1)%7)
    last = date.fromisoformat(days[-1]['date'])
    if mobile: first = max(first,last-timedelta(days=(last.weekday()+1)%7+25*7))
    cell,step = (10,15) if mobile else (12,16)
    gx,gy = (x if mobile else x+18),282
    palette = [PANEL,'#123E40','#14736E','#20A89B',TEAL]
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
    c = text(x,37,'05 / CONNECT',13,TEAL,600,True)
    c += text(x,83,"Let's build something useful.",25 if mobile else 36,WHITE,700)
    c += text(x,121,'Applied AI / Computer vision / Practical tools',15 if mobile else 20,MUTED)
    c += line(x,145,w-x,145,TEAL) + text(x,179,'GITHUB / AMMARCHO',13 if mobile else 17,TEAL,600,True)
    save('connect'+('-mobile' if mobile else ''),w,204,c,'Connect with Ammar on GitHub. Applied AI, computer vision and practical tools.')


def build_readme():
    def picture(slug,alt,href=None):
        value = f'<picture>\n  <source media="(max-width: 600px)" srcset="assets/{slug}-mobile.svg" />\n  <img src="assets/{slug}.svg" width="100%" alt="{escape(alt,quote=True)}" />\n</picture>'
        return f'<a href="{href}">\n{value}\n</a>' if href else value
    parts = [picture('applied-ai-lab',"Hi, I'm Ammar. Applied AI Lab. Turning models into useful tools. Information Technology at UGM."),
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
        save('selected-work'+('-mobile' if mobile else ''),w,82,text(x,52,'02 / SELECTED WORK',20 if mobile else 26,TEAL,600,True),'02 / Selected work')
        for project in PROJECTS: build_project(project,mobile)
        build_stack(mobile)
        stats = build_activity(days,user['public_repos'],mobile)
        build_footer(mobile)
    build_readme()
    print(json.dumps({'calendar_start':days[0]['date'],'calendar_end':days[-1]['date'],'days':len(days),**stats}))


if __name__=='__main__': main()
