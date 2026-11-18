"""Deterministic, code-drawn environmental art for the Hex World laboratory.

No raster source files are loaded. Each profile is rendered onto a transparent,
supersampled Pygame surface and reduced once for clean edges.
"""
from __future__ import annotations

import pygame


def _surface(size: tuple[int, int], scale: int = 3) -> pygame.Surface:
    return pygame.Surface((size[0] * scale, size[1] * scale), pygame.SRCALPHA)


def _finish(canvas: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
    return pygame.transform.smoothscale(canvas, size)


def _tree() -> pygame.Surface:
    size, s = (132, 168), 3
    image = _surface(size, s)
    def p(x, y): return round(x*s), round(y*s)
    def poly(color, points, width=0):
        pygame.draw.polygon(image, color, [p(x, y) for x, y in points], width=width*s)
    def ellipse(color, rect):
        x, y, w, h = rect
        pygame.draw.ellipse(image, color, pygame.Rect(round(x*s), round(y*s), round(w*s), round(h*s)))
    def line(color, points, width=1):
        pygame.draw.lines(image, color, False, [p(x, y) for x, y in points], max(1, width*s))

    # Contact shadow, roots and a tapered, forked trunk.
    ellipse((13, 20, 29, 8), (22, 145, 88, 15))
    poly((73, 45, 31), [(54,147),(43,158),(31,159),(42,151),(48,143)])
    poly((92, 58, 36), [(65,147),(77,157),(94,159),(81,150),(74,142)])
    poly((111, 73, 43), [(58,145),(51,155),(44,157),(55,148)])
    poly((54,35,27), [(49,151),(54,111),(52,82),(45,57),(55,48),(66,74),(72,48),(82,54),(76,89),(81,119),(87,151),(72,156),(63,151)])
    poly((126,78,43), [(53,149),(58,111),(57,81),(50,58),(56,53),(64,83),(67,119),(68,151)])
    poly((83,47,31), [(68,151),(70,115),(68,82),(74,56),(81,57),(77,91),(81,121),(87,151)])
    # Branches remain visible through gaps in the crown.
    poly((83,48,30), [(61,103),(53,79),(36,64),(31,51),(39,61),(58,73),(68,95)])
    poly((100,59,34), [(70,96),(82,74),(99,61),(104,47),(101,64),(84,84),(77,105)])
    poly((91,51,31), [(62,83),(61,59),(51,43),(55,37),(68,59),(70,82)])
    line((183,119,65), [(57,137),(61,119),(60,103),(64,91)], 2)
    line((47,31,25), [(76,137),(73,119),(76,105)], 2)
    line((151,91,49), [(54,151),(45,156),(39,156)], 2)
    line((57,35,27), [(78,151),(87,157),(92,157)], 2)
    ellipse((54,31,25), (61,116,5,8))
    ellipse((179,112,61), (62,118,2,3))

    shadows = [
        (15,54,47,48,(34,83,48)), (37,27,55,57,(43,105,54)),
        (67,18,49,53,(37,91,49)), (88,43,34,46,(31,76,43)),
        (7,83,48,43,(36,91,48)), (39,75,58,57,(34,88,46)),
        (78,82,47,47,(28,73,41)), (26,112,45,28,(34,78,43)),
    ]
    for x,y,w,h,color in shadows:
        ellipse(color,(x,y,w,h))
    lit = [
        (23,60,31,29,(72,139,66)), (45,34,35,35,(83,151,70)),
        (75,29,29,31,(67,132,62)), (91,55,22,27,(57,119,57)),
        (14,88,29,25,(70,132,62)), (45,83,35,34,(72,143,66)),
        (78,91,29,27,(61,123,57)),
    ]
    for x,y,w,h,color in lit:
        ellipse(color,(x,y,w,h))
    for x,y,w,h in ((31,67,8,5),(48,47,10,6),(68,35,8,5),(89,57,7,5),
                    (21,95,8,5),(52,91,9,5),(78,102,8,5),(39,119,7,4)):
        ellipse((139,190,91),(x,y,w,h))
    for x,y in ((39,76),(69,68),(93,83),(55,112)):
        ellipse((25,65,38),(x,y,9,7))
    return _finish(image,size)


def _rock() -> pygame.Surface:
    size,s=(66,48),3
    image=_surface(size,s)
    def p(x,y): return round(x*s),round(y*s)
    def poly(color,points,width=0):
        pygame.draw.polygon(image,color,[p(x,y) for x,y in points],width=width*s)
    def ellipse(color,rect):
        x,y,w,h=rect
        pygame.draw.ellipse(image,color,pygame.Rect(round(x*s),round(y*s),round(w*s),round(h*s)))
    ellipse((12,18,27,9),(5,34,57,10))
    silhouette=[(5,31),(9,18),(20,8),(34,5),(47,12),(61,25),(57,37),(43,42),(17,40)]
    poly((47,54,65),silhouette)
    poly((139,151,160),[(9,20),(20,8),(34,5),(29,22),(18,30),(5,31)])
    poly((105,119,132),[(34,5),(47,12),(61,25),(43,27),(29,22)])
    poly((72,84,99),[(5,31),(18,30),(29,22),(43,27),(57,37),(43,42),(17,40)])
    poly((170,181,188),[(20,8),(34,5),(29,14),(17,18)])
    poly((48,59,72),[(43,27),(61,25),(57,37),(43,42),(38,33)])
    poly((33,40,51),silhouette,1)
    pygame.draw.lines(image,(74,87,102),False,[p(29,22),p(38,33),p(43,42)],2*s)
    pygame.draw.lines(image,(192,200,205),False,[p(12,20),p(21,12),p(28,10)],1*s)
    pygame.draw.line(image,(58,69,82),p(17,31),p(26,35),1*s)
    pygame.draw.circle(image,(205,211,210),p(23,17),1*s)
    pygame.draw.circle(image,(120,132,143),p(49,28),1*s)
    return _finish(image,size)


def _bush() -> pygame.Surface:
    size,s=(88,58),3
    image=_surface(size,s)
    def ellipse(color,rect):
        x,y,w,h=rect
        pygame.draw.ellipse(image,color,pygame.Rect(round(x*s),round(y*s),round(w*s),round(h*s)))
    ellipse((13,20,29,8),(8,43,72,12))
    ellipse((25,68,39),(7,19,72,34))
    masses=[
        (8,21,31,29,(38,91,48)),(20,10,34,36,(48,113,56)),
        (43,13,35,35,(36,91,49)),(54,26,27,25,(30,77,43)),
        (27,27,34,27,(54,124,60)),(4,32,29,20,(42,100,50)),
    ]
    for x,y,w,h,color in masses:
        ellipse(color,(x,y,w,h))
    for x,y,w,h in ((17,23,12,8),(31,15,13,8),(51,19,10,7),
                    (29,34,12,7),(62,31,8,6),(10,38,9,5)):
        ellipse((111,174,82),(x,y,w,h))
    for x,y in ((27,30),(48,38),(65,28)):
        ellipse((24,65,37),(x,y,5,4))
    return _finish(image,size)


def build_environment_surfaces() -> dict[str, pygame.Surface]:
    """Create all three environment visuals from deterministic drawing code."""
    return {"tree":_tree(),"rock":_rock(),"bush":_bush()}
