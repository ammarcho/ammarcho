"""Self-contained animated SVG spider that visits real contribution cells."""
from html import escape


def plan_route(cells):
    """Visit active cells with grid-adjacent steps, then return to the entrance."""
    food = {(c['col'], c['row']) for c in cells if c['count'] > 0}
    remaining = set(food)
    route = [(-1, 3)]
    visited = {}

    def move_to(target):
        x, y = route[-1]
        tx, ty = target
        while (x, y) != target:
            if x != tx:
                x += 1 if tx > x else -1
            else:
                y += 1 if ty > y else -1
            route.append((x, y))
            if (x, y) in remaining:
                visited[(x, y)] = len(route) - 1
                remaining.remove((x, y))

    while remaining:
        x, y = route[-1]
        target = min(remaining, key=lambda p: (abs(p[0]-x)+abs(p[1]-y), p[0], p[1]))
        move_to(target)
    move_to((-1, 3))
    if len(route) == 1:
        route.extend([(0, 3), (-1, 3)])
    assert set(visited) == food
    assert all(abs(a[0]-b[0])+abs(a[1]-b[1]) == 1 for a,b in zip(route,route[1:]))
    return route, visited


def render(cells, gx, gy, step, cell, palette):
    route, eaten = plan_route(cells)
    duration = max(24, min(72, len(route)*.20))
    styles = [
        '@keyframes spider-step-a{0%,100%{transform:rotate(-7deg)}50%{transform:rotate(7deg)}}',
        '@keyframes spider-step-b{0%,100%{transform:rotate(7deg)}50%{transform:rotate(-7deg)}}',
        '.spider-legs-a,.spider-legs-b{transform-box:fill-box;transform-origin:center}',
        '.spider-legs-a{animation:spider-step-a .24s ease-in-out infinite}',
        '.spider-legs-b{animation:spider-step-b .24s ease-in-out infinite}',
        '@media(prefers-reduced-motion:reduce){.spider-runner{display:none}.contribution-cell{animation:none!important}}',
    ]
    content = []
    for i,c in enumerate(cells):
        col,row = c['col'],c['row']
        color = palette[c['level']]
        anim = ''
        if (col,row) in eaten:
            when = 90*eaten[(col,row)]/(len(route)-1)
            styles.append(f'@keyframes spider-eat-{i}{{0%,{max(0,when-.01):.4f}%{{fill:{color}}}{when:.4f}%,94%{{fill:{palette[0]}}}97%,100%{{fill:{color}}}}}')
            anim = f' style="animation:spider-eat-{i} {duration}s linear infinite"'
        title = escape(f"{c['date']}: {c['count']} contributions")
        content.append(f'<rect class="contribution-cell" data-date="{c["date"]}" data-count="{c["count"]}" x="{gx+col*step}" y="{gy+row*step}" width="{cell}" height="{cell}" rx="2" fill="{color}" stroke="#4169AF" stroke-width=".4"{anim}><title>{title}</title></rect>')
    # The spider faces +x; animateMotion rotates it naturally along the route.
    path = 'M'+' L'.join(f'{gx+x*step+cell/2:g} {gy+y*step+cell/2:g}' for x,y in route)
    legs_a,legs_b = [],[]
    for side in [-1,1]:
        for i,(ax,kx,fx) in enumerate([(-5,-10,-13),(-2,-5,-7),(2,5,7),(5,10,13)]):
            leg=f'<path d="M{ax} {side*3}L{kx} {side*8}L{fx} {side*13}"/>'
            (legs_a if (i+(side==1))%2 else legs_b).append(leg)
    spider = '<g class="spider-runner" aria-label="A red and blue spider crawling through contribution cells">'
    spider += f'<animateMotion dur="{duration}s" repeatCount="indefinite" path="{path}" rotate="auto" keyPoints="0;1;1" keyTimes="0;0.90;1" calcMode="linear"/>'
    spider += '<path d="M-8 0Q-15-3-23 0" fill="none" stroke="#FFF9EE" stroke-width=".8" opacity=".55"/>'
    for cls,legs in [('a',legs_a),('b',legs_b)]:
        spider += f'<g class="spider-legs-{cls}" fill="none" stroke="#FFF9EE" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'+''.join(legs)+'</g>'
    spider += '<ellipse cx="-3" cy="0" rx="7" ry="5.5" fill="#E62429" stroke="#030D25" stroke-width="1.3"/>'
    spider += '<path d="M-8 0H1M-3-5V5M-7-3L1 3M-7 3L1-3" stroke="#030D25" stroke-width=".6" fill="none"/>'
    spider += '<ellipse cx="4" cy="0" rx="4.5" ry="4" fill="#1559B7" stroke="#030D25" stroke-width="1.2"/>'
    spider += '<ellipse cx="8" cy="0" rx="3.3" ry="3.7" fill="#E62429" stroke="#030D25" stroke-width="1"/>'
    spider += '<path d="M8-2.6L10.7-1.1L8.2-.4ZM8 2.6L10.7 1.1L8.2 .4Z" fill="#FFF9EE"/>'
    spider += '</g>'
    return '<style>'+''.join(styles)+'</style>'+''.join(content)+spider, {'steps':len(route)-1,'visited':len(eaten),'duration_seconds':duration}
