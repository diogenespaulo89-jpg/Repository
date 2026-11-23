"""
Gera os modelos 3D (formato .3mf) dos 4 produtos do catálogo inicial de maquetes.

Todos os projetos são FICTÍCIOS e foram criados para este catálogo.
Unidades em milímetros. Uso:

    pip install trimesh manifold3d shapely mapbox_earcut matplotlib lxml
    python gerar_modelos.py                # gera tudo em ./3mf
    python gerar_modelos.py --unidade "APTO 1204"   # personaliza a miniatura
"""
import argparse
import json
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, Manifold, OpType
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

SEG = 32  # segmentos de círculos


# ---------------------------------------------------------------- utilitários
def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def cyl(x, y, z, h, r, r_top=None, seg=SEG):
    return Manifold.cylinder(h, r, r if r_top is None else r_top, seg).translate((x, y, z))


def union(parts):
    parts = [p for p in parts if p is not None]
    return parts[0] if len(parts) == 1 else Manifold.batch_boolean(parts, OpType.Add)


def subtract(base, cuts):
    cuts = [c for c in cuts if c is not None]
    return base if not cuts else base - union(cuts)


def tree(x, y, z, h, r):
    """Árvore estilizada: tronco + copa cônica (imprime sem suporte)."""
    trunk_h = h * 0.25
    return union([cyl(x, y, z, trunk_h, r * 0.22, seg=12),
                  cyl(x, y, z + trunk_h, h - trunk_h, r, 0.15, seg=24)])


def text3d(s, size, height, weight="bold"):
    """Texto em relevo (base em z=0), com origem no canto inferior esquerdo."""
    tp = TextPath((0, 0), s, size=size, prop=FontProperties(family="DejaVu Sans", weight=weight))
    polys = []
    for p in tp.to_polygons():
        p = np.asarray(p)
        if len(p) > 1 and np.allclose(p[0], p[-1]):
            p = p[:-1]
        if len(p) >= 3:
            polys.append(p.tolist())
    cs = CrossSection(polys, FillRule.EvenOdd)
    return cs.extrude(height)


def centered_text(s, size, height, cx, y, z):
    t = text3d(s, size, height)
    (x0, y0, _), (x1, y1, _) = np.array(t.bounding_box()[:3]), np.array(t.bounding_box()[3:])
    return t.translate((cx - (x0 + x1) / 2, y - y0, z))


def to_trimesh(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    return trimesh.Trimesh(v, f, process=False)


def drop_to_bed(m):
    b = m.bounding_box()
    return m.translate((-b[0], -b[1], -b[2]))


def export_3mf(path, objects):
    """objects: lista de (nome, Manifold). Cada um vira um objeto no 3MF."""
    scene = trimesh.Scene()
    for name, m in objects:
        scene.add_geometry(to_trimesh(m), geom_name=name, node_name=name)
    scene.export(path, file_type="3mf")


def arrange(parts, gap=8.0):
    """Coloca peças lado a lado (para o arquivo de 'visão geral')."""
    out, x = [], 0.0
    for name, m in parts:
        m = drop_to_bed(m).translate((x, 0, 0))
        b = m.bounding_box()
        x = b[3] + gap
        out.append((name, m))
    return out


def info(m):
    b = m.bounding_box()
    return {
        "dimensoes_mm": [round(b[3] - b[0], 1), round(b[4] - b[1], 1), round(b[5] - b[2], 1)],
        "volume_cm3": round(m.volume() / 1000, 1),
    }


# ============================================================ PRODUTO 1
# Casa Ipê — sobrado contemporâneo, escala 1:100 (projeto fictício)
def casa_alto_padrao():
    H1 = 30.0       # pé-direito térreo (3,0 m)
    T = 2.0         # espessura parede externa
    TI = 1.5        # parede interna
    BZ = 4.0        # espessura do terreno
    X0, X1, Y0, Y1 = 25, 175, 40, 150          # térreo 15 x 11 m
    UX0, UX1, UY0, UY1 = 55, 185, 50, 145      # superior 13 x 9,5 m (balanço de 1 m)
    PIN_D, PIN_H, HOLE_D = 2.5, 1.8, 2.9

    # ---- Peça A: terreno + térreo
    base = box(0, 0, 0, 200, 160, BZ)
    pool = box(30, 8, BZ - 2.5, 110, 30, BZ + 1)
    pool_rim = subtract(box(28, 6, BZ, 112, 32, BZ + 1.0), [box(30, 8, BZ - 1, 110, 30, BZ + 2)])
    terreno = union([subtract(base, [pool]), pool_rim])

    zt = BZ
    ext = subtract(box(X0, Y0, zt, X1, Y1, zt + H1), [box(X0 + T, Y0 + T, zt - 1, X1 - T, Y1 - T, zt + H1 + 1)])
    win = []
    # frente (y = 40), voltada à piscina: grandes panos de vidro
    win += [box(35, Y0 - 1, zt + 2, 90, Y0 + T + 1, zt + 26), box(105, Y0 - 1, zt + 8, 165, Y0 + T + 1, zt + 26)]
    # fundos (y = 150)
    win += [box(x, Y1 - T - 1, zt + 10, x + 20, Y1 + 1, zt + 24) for x in (40, 110, 145)]
    # laterais
    win += [box(X0 - 1, y, zt + 10, X0 + T + 1, y + 20, zt + 24) for y in (60, 110)]
    win += [box(X1 - T - 1, 60, zt + 2, X1 + 1, 90, zt + 26), box(X1 - T - 1, 115, zt + 10, X1 + 1, 135, zt + 24)]
    ext = subtract(ext, win)

    hi = H1 - 2  # paredes internas mais baixas que as externas
    inner = [
        subtract(box(95, Y0 + T, zt, 95 + TI, Y1 - T, zt + hi), [box(94, 70, zt, 97, 79, zt + 22)]),
        subtract(box(95, 100, zt, X1 - T, 100 + TI, zt + hi), [box(130, 99, zt, 139, 102, zt + 22)]),
    ]
    blocks, pins_a = [], []
    for cx, cy in ((29.5, 44.5), (170.5, 44.5), (29.5, 145.5), (170.5, 145.5)):
        blocks.append(box(cx - 2.5, cy - 2.5, zt, cx + 2.5, cy + 2.5, zt + H1))
        pins_a.append((cx, cy))
    pins = [cyl(cx, cy, zt + H1, PIN_H, PIN_D / 2) for cx, cy in pins_a]
    trees = [tree(x, y, BZ, 16, 6) for x, y in ((12, 60), (12, 125), (190, 22), (150, 16), (190, 150))]
    peca_a = union([terreno, ext] + inner + blocks + pins + trees)

    # ---- Peça B: laje + pavimento superior (impressa com a laje sobre a mesa)
    LZ = 2.5
    H2 = 28.0
    laje = union([box(X0, Y0, 0, X1, Y1, LZ), box(X1 - 1, UY0, 0, UX1, UY1, LZ)])
    laje = subtract(laje, [cyl(cx, cy, -1, LZ + 1 - 0.0, HOLE_D / 2) for cx, cy in pins_a])
    up = subtract(box(UX0, UY0, LZ, UX1, UY1, LZ + H2),
                  [box(UX0 + T, UY0 + T, LZ - 1, UX1 - T, UY1 - T, LZ + H2 + 1)])
    uwin = [box(65, UY0 - 1, LZ + 6, 175, UY0 + T + 1, LZ + 24)]
    uwin += [box(x, UY1 - T - 1, LZ + 10, x + 20, UY1 + 1, LZ + 24) for x in (70, 120, 155)]
    uwin += [box(UX0 - 1, y, LZ + 10, UX0 + T + 1, y + 20, LZ + 24) for y in (65, 110)]
    uwin += [box(UX1 - T - 1, 70, LZ + 6, UX1 + 1, 125, LZ + 24)]
    up = subtract(up, uwin)
    uin = [subtract(box(x, UY0 + T, LZ, x + TI, UY1 - T, LZ + H2 - 2), [box(x - 1, 125, LZ, x + 3, 134, LZ + 22)])
           for x in (100, 140)]
    ublocks, upins = [], []
    for cx, cy in ((59.5, 54.5), (180.5, 54.5), (59.5, 140.5), (180.5, 140.5)):
        ublocks.append(box(cx - 2.5, cy - 2.5, LZ, cx + 2.5, cy + 2.5, LZ + H2))
        upins.append((cx, cy))
    pins_b = [cyl(cx, cy, LZ + H2, PIN_H, PIN_D / 2) for cx, cy in upins]
    # guarda-corpo do terraço (sobre a laje do térreo, à esquerda do volume superior)
    rail = [box(X0, Y0, LZ, UX0, Y0 + 1.2, LZ + 9), box(X0, Y0, LZ, X0 + 1.2, Y1, LZ + 9),
            box(X0, Y1 - 1.2, LZ, UX0, Y1, LZ + 9)]
    peca_b = union([laje, up] + uin + ublocks + pins_b + rail)

    # ---- Peça C: cobertura com platibanda
    RZ = 2.0
    cob = box(UX0 - 2, UY0 - 2, 0, UX1 + 2, UY1 + 2, RZ)
    cob = subtract(cob, [cyl(cx, cy, -1, RZ + 2, HOLE_D / 2) for cx, cy in upins])
    plat = subtract(box(UX0 - 2, UY0 - 2, RZ, UX1 + 2, UY1 + 2, RZ + 4),
                    [box(UX0 - 0.5, UY0 - 0.5, RZ - 1, UX1 + 0.5, UY1 + 0.5, RZ + 5)])
    peca_c = union([cob, plat, box(80, 80, RZ, 110, 100, RZ + 3)])  # volume técnico/claraboia

    parts = [("A_terreno_e_terreo", peca_a), ("B_laje_e_pavimento_superior", peca_b), ("C_cobertura", peca_c)]
    montado = [("A_terreno_e_terreo", peca_a),
               ("B_laje_e_pavimento_superior", peca_b.translate((0, 0, zt + H1))),
               ("C_cobertura", peca_c.translate((0, 0, zt + H1 + LZ + H2)))]
    return parts, montado


# ============================================================ PRODUTO 2
# Condomínio Recanto das Palmeiras — condomínio horizontal, escala 1:500 (fictício)
def casa_a():
    """Sobrado com telhado de duas águas: 8 x 10 m (16 x 20 mm)."""
    body = box(0, 0, 0, 16, 20, 11)
    roof = Manifold.batch_hull([box(-0.6, -0.6, 11, 16.6, 20.6, 11.4), box(7.7, -0.6, 15.5, 8.3, 20.6, 15.6)])
    det = [box(2, -0.1, 6.5, 6, 0.5, 9.5), box(10, -0.1, 6.5, 14, 0.5, 9.5),     # janelas
           box(2, -0.1, 0, 8, 0.5, 4.5), box(11, -0.1, 0, 14, 0.5, 5)]           # garagem e porta
    return subtract(union([body, roof]), det)


def casa_b():
    """Casa contemporânea com dois volumes e laje plana: 8 x 10 m."""
    low = box(0, 0, 0, 16, 20, 6)
    high = box(4, 3, 6, 16, 20, 12)
    plat = subtract(box(4, 3, 12, 16, 20, 13), [box(4.8, 3.8, 11.5, 15.2, 19.2, 14)])
    det = [box(1.5, -0.1, 0, 8, 0.5, 4.5), box(6, 2.9, 7.5, 14, 3.5, 10.5), box(10, -0.1, 1, 14.5, 0.5, 4.5)]
    return subtract(union([low, high, plat]), det)


def condominio():
    BZ = 3.0
    S = 400.0
    base = box(0, 0, 0, S, S, BZ)
    feats = []
    # muro perimetral com abertura da portaria
    W, WH = 2.0, 5.0
    muro = union([box(0, 0, BZ, S, W, BZ + WH), box(0, S - W, BZ, S, S, BZ + WH),
                  box(0, 0, BZ, W, S, BZ + WH), box(S - W, 0, BZ, S, S, BZ + WH)])
    muro = subtract(muro, [box(188, -1, BZ - 1, 212, W + 1, BZ + WH + 1)])
    feats.append(muro)
    # portaria e canteiro central da avenida
    feats += [box(198.5, 20, BZ, 201.5, 306, BZ + 0.8), box(195, 5, BZ, 205, 15, BZ + 7),
              box(193.5, 3.5, BZ + 7, 206.5, 16.5, BZ + 7.8)]
    feats += [tree(200, y, BZ + 0.8, 6, 1.4) for y in range(40, 300, 30)]
    # quadras e lotes
    lot_w, lot_d, gap = 24.0, 40.0, 0.6
    pockets, lots = [], []
    lot_centers = []
    for yb in (18, 114, 210):                    # cada quadra = 2 fileiras de lotes
        for row in range(2):
            y0 = yb + row * lot_d
            front_low = (row == 0)               # fileira de baixo faz frente para a rua de baixo
            for xs in (19, 213):
                for i in range(7):
                    x0 = xs + i * lot_w
                    lots.append(box(x0 + gap / 2, y0 + gap / 2, BZ, x0 + lot_w - gap / 2, y0 + lot_d - gap / 2, BZ + 1.2))
                    cx = x0 + lot_w / 2
                    py0 = y0 + 4 if front_low else y0 + lot_d - 4 - 20.6
                    pockets.append(box(cx - 8.3, py0, BZ + 0.4, cx + 8.3, py0 + 20.6, BZ + 2))
                    lot_centers.append((cx, py0, front_low))
    feats.append(subtract(union(lots), pockets))
    # área de lazer
    lazer = box(20, 310, BZ, 380, 394, BZ + 0.8)
    pool = box(150, 330, BZ - 1.5, 200, 352, BZ + 2)
    feats.append(subtract(lazer, [pool]))
    feats.append(subtract(box(148, 328, BZ + 0.8, 202, 354, BZ + 1.4), [box(150, 330, BZ, 200, 352, BZ + 3)]))
    clube = union([box(215, 335, BZ + 0.8, 265, 372, BZ + 10.8), box(213, 333, BZ + 10.8, 267, 374, BZ + 11.6)])
    clube = subtract(clube, [box(220, 334, BZ + 2, 260, 336, BZ + 8)])          # fachada envidraçada
    feats.append(clube)
    quadra = subtract(box(285, 328, BZ + 0.8, 325, 352, BZ + 1.2), [box(286, 329, BZ, 324, 351, BZ + 2)])
    feats += [quadra, box(304.6, 328, BZ + 0.8, 305.4, 352, BZ + 1.2)]
    feats += [tree(x, y, BZ + 0.8, 9, 3) for x, y in
              ((40, 330), (60, 375), (90, 340), (120, 380), (130, 325), (215, 385), (280, 385),
               (340, 330), (360, 370), (100, 360), (45, 355), (345, 385))]
    feats.append(base)
    full = union(feats)

    tiles = []
    for nome, (x0, y0) in (("1_frente_esquerda", (0, 0)), ("2_frente_direita", (200, 0)),
                           ("3_fundo_esquerda", (0, 200)), ("4_fundo_direita", (200, 200))):
        t = full ^ box(x0, y0, -1, x0 + 200, y0 + 200, 50)
        tiles.append(("base_" + nome, t))

    ca, cb = casa_a(), casa_b()
    # placa com 20 casas (10 de cada modelo) para impressão em lote
    lote = []
    for j in range(4):
        for i in range(5):
            m = ca if (i + j) % 2 == 0 else cb
            lote.append(m.translate((i * 26, j * 30, 0)))
    placa_casas = union(lote)

    parts = tiles + [("casa_modelo_A", ca), ("casa_modelo_B", cb), ("placa_20_casas", placa_casas)]
    # visão montada: base + 40 casas (lotes restantes ficam livres, como "à venda")
    montado = [("base_completa", full)]
    casas = []
    for k, (cx, py0, front_low) in enumerate(lot_centers):
        if k % 2 == 1:
            continue
        m = ca if (k // 2) % 2 == 0 else cb
        if not front_low:  # gira a casa para fazer frente para a rua de cima
            m = m.rotate((0, 0, 180)).translate((16, 20, 0))
        casas.append(m.translate((cx - 8, py0 + 0.3, BZ + 0.4)))
    montado.append(("casas_42", union(casas)))
    return parts, montado


# ============================================================ PRODUTO 3
# Residencial Aurora — torre de 14 pavimentos-tipo, escala 1:200 (fictício)
W, D = 110.0, 80.0         # 22 x 16 m
T = 2.0
PIL = 4.0
HM = 15.0                  # 3,0 m por pavimento
PIN_D, PIN_H, HOLE_D, HOLE_H = 2.2, 2.0, 2.6, 2.5
PILARES = [(T + PIL / 2, T + PIL / 2), (W - T - PIL / 2, T + PIL / 2),
           (T + PIL / 2, D - T - PIL / 2), (W - T - PIL / 2, D - T - PIL / 2)]


def pavimento_tipo():
    walls = subtract(box(0, 0, 0, W, D, HM), [box(T, T, -1, W - T, D - T, HM + 1)])
    laje = subtract(box(0, 0, 0, W, D, 1.2), [box(6, 6, -1, W - 6, D - 6, 2)])  # anel: luz do LED passa
    sacada = box(8, -8, 0, 102, 0.01, 1.2)
    guarda = union([box(8, -8, 1.2, 102, -7.2, 5.5), box(8, -8, 1.2, 8.8, 0, 5.5), box(101.2, -8, 1.2, 102, 0, 5.5)])
    cuts = [box(12, -1, 1.2, 50, T + 1, 12.5), box(60, -1, 1.2, 98, T + 1, 12.5)]          # portas das sacadas
    cuts += [box(10 + i * 13.5, D - T - 1, 4, 18 + i * 13.5, D + 1, 12) for i in range(7)]  # fundos
    for x in (-1, W - T - 1):
        cuts += [box(x, y0, 4, x + T + 2, y1, 12) for y0, y1 in ((12, 22), (30, 50), (58, 68))]
    pil = [box(cx - PIL / 2, cy - PIL / 2, 0, cx + PIL / 2, cy + PIL / 2, HM) for cx, cy in PILARES]
    body = subtract(union([walls, laje, sacada, guarda] + pil), cuts)
    holes = [cyl(cx, cy, -1, HOLE_H + 1, HOLE_D / 2) for cx, cy in PILARES]
    pins = [cyl(cx, cy, HM, PIN_H, PIN_D / 2) for cx, cy in PILARES]
    return union([subtract(body, holes)] + pins)


def terreo_aurora():
    BZ = 4.0
    HT = 22.5
    plinto = box(-25, -35, 0, 135, 95, BZ)
    plinto = subtract(plinto, [cyl(55, 40, -1, BZ + 2, 4), box(52, 40, -1, 58, 96, 2.5)])  # passagem do cabo do LED
    walls = subtract(box(0, 0, BZ, W, D, BZ + HT), [box(T, T, BZ - 1, W - T, D - T, BZ + HT + 1)])
    cuts = [box(8, -1, BZ, 102, T + 1, BZ + 19)]                                  # hall envidraçado
    cuts += [box(8, D - T - 1, BZ + 3, 102, D + 1, BZ + 19)]
    cuts += [box(x, 8, BZ + 3, x + T + 2, 72, BZ + 19) for x in (-1, W - T - 1)]
    walls = subtract(walls, cuts)
    pil = [box(cx - PIL / 2, cy - PIL / 2, BZ, cx + PIL / 2, cy + PIL / 2, BZ + HT) for cx, cy in PILARES]
    pins = [cyl(cx, cy, BZ + HT, PIN_H, PIN_D / 2) for cx, cy in PILARES]
    marquise_pilares = [box(x, -20, BZ, x + 2, -18, BZ + 18) for x in (35, 73)]
    marquise = box(33, -21, BZ + 18, 77, 1, BZ + 19.5)  # apoiada nos pilares e na fachada
    nome = centered_text("RESIDENCIAL AURORA", 7, 0.8, 55, -31.5, BZ)
    jardim = [tree(x, y, BZ, 18, 6) for x, y in ((-14, -20), (124, -20), (-14, 80), (124, 80), (10, -24), (100, -24))]
    calcada = box(40, -35, BZ, 70, -22, BZ + 0.4)
    return union([plinto, walls, nome, calcada, marquise, *marquise_pilares] + pil + pins + jardim), BZ + HT


def cobertura_aurora():
    slab = box(0, 0, 0, W, D, 5)
    slab = subtract(slab, [cyl(cx, cy, -1, HOLE_H + 1, HOLE_D / 2) for cx, cy in PILARES])
    plat = subtract(box(0, 0, 5, W, D, 9), [box(T, T, 4, W - T, D - T, 10)])
    maq = box(37, 28, 5, 73, 52, 15)
    caixa = box(45, 33, 15, 65, 47, 20)
    pergola = [box(10, 10 + i * 6, 5, 30, 11 + i * 6, 9) for i in range(5)]
    return union([slab, plat, maq, caixa] + pergola)


def torre():
    terreo, zt = terreo_aurora()
    pav = pavimento_tipo()
    cob = cobertura_aurora()
    parts = [("A_terreo_com_jardim", terreo), ("B_pavimento_tipo_imprimir_14x", pav), ("C_cobertura", cob)]
    montado = [("A_terreo_com_jardim", terreo)]
    for i in range(14):
        montado.append((f"pavimento_{i + 1:02d}", pav.translate((0, 0, zt + i * HM))))
    montado.append(("C_cobertura", cob.translate((0, 0, zt + 14 * HM))))
    return parts, montado


# ============================================================ PRODUTO 4
# Miniatura-presente da fachada do Residencial Aurora (~ 1:600)
def miniatura(unidade="APTO 101 · 2026"):
    PZ = 8.0
    placa = Manifold.batch_hull([box(0, 0, 0, 76, 52, PZ - 1.5), box(1.5, 1.5, 0, 74.5, 50.5, PZ)])
    tw, td, th = 36.0, 26.0, 80.0
    tx, ty = (76 - tw) / 2, 22.0
    corpo = box(tx, ty, PZ, tx + tw, ty + td, PZ + th)
    rec = []
    n_and = 15
    hp = (th - 8) / n_and
    for k in range(n_and):
        z = PZ + 6 + k * hp
        # janelas em baixo-relevo nas laterais e nos fundos
        for i in range(4):
            rec.append(box(tx + 3 + i * 8.2, ty + td - 0.5, z + 1, tx + 8 + i * 8.2, ty + td + 1, z + 3.6))
        for x in (tx - 1, tx + tw - 0.5):
            for j in range(3):
                rec.append(box(x, ty + 3 + j * 7.5, z + 1, x + 1.5, ty + 7.5 + j * 7.5, z + 3.6))
        # vidros das sacadas na frente
        rec.append(box(tx + 3, ty - 1, z + 0.8, tx + tw - 3, ty + 0.5, z + 3.8))
    corpo = subtract(corpo, rec)
    sacadas = [box(tx + 2, ty - 1.0, PZ + 6 + k * hp, tx + tw - 2, ty + 0.1, PZ + 6 + k * hp + 0.8)
               for k in range(n_and)]
    hall = box(tx + 6, ty - 0.6, PZ, tx + tw - 6, ty + 0.1, PZ + 4)
    topo = [box(tx + 10, ty + 7, PZ + th, tx + tw - 10, ty + td - 7, PZ + th + 5),
            box(tx + 13, ty + 9, PZ + th + 5, tx + tw - 13, ty + td - 9, PZ + th + 8)]
    t1 = centered_text("RESIDENCIAL AURORA", 5.2, 0.6, 38, 11.5, PZ)
    t2 = centered_text(unidade, 4.0, 0.6, 38, 4.0, PZ)
    return [("miniatura_aurora", union([placa, corpo, hall] + sacadas + topo)),
            ("texto_em_relevo_cor2", union([t1, t2]))]


# ============================================================ preview
def render_png(path, objects, elev=28, azim=-60, title=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(8, 6), dpi=130)
    ax = fig.add_subplot(111, projection="3d")
    light = np.array([0.4, -0.6, 0.8]); light /= np.linalg.norm(light)
    palette = [(0.93, 0.92, 0.88), (0.80, 0.84, 0.90), (0.88, 0.84, 0.78), (0.83, 0.89, 0.83)]
    allv = []
    for idx, (_, m) in enumerate(objects):
        tm = to_trimesh(m)
        tri = tm.vertices[tm.faces]
        n = tm.face_normals
        shade = 0.45 + 0.55 * np.clip(n @ light, 0, 1)
        base = np.array(palette[idx % len(palette)])
        colors = np.clip(shade[:, None] * base, 0, 1)
        ax.add_collection3d(Poly3DCollection(tri, facecolors=colors, edgecolors="none"))
        allv.append(tm.vertices)
    v = np.vstack(allv)
    mn, mx = v.min(0), v.max(0)
    ax.set_xlim(mn[0], mx[0]); ax.set_ylim(mn[1], mx[1]); ax.set_zlim(mn[2], mx[2])
    ax.set_box_aspect(mx - mn)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=11)
    plt.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


# ============================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "3mf"))
    ap.add_argument("--previews", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "previews"))
    ap.add_argument("--unidade", default="APTO 101 · 2026")
    ap.add_argument("--sem-preview", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)
    os.makedirs(a.previews, exist_ok=True)

    resumo = {}
    produtos = {
        "1_casa_ipe_1-100": casa_alto_padrao(),
        "2_condominio_recanto_1-500": condominio(),
        "3_torre_aurora_1-200": torre(),
    }
    mini = miniatura(a.unidade)
    produtos["4_miniatura_aurora"] = (mini, mini)

    for prod, (parts, montado) in produtos.items():
        d = os.path.join(a.saida, prod)
        os.makedirs(d, exist_ok=True)
        resumo[prod] = {}
        if prod == "4_miniatura_aurora":
            completa = union([m for _, m in mini])
            export_3mf(os.path.join(d, "miniatura_completa_1_cor.3mf"), [("miniatura_completa", completa)])
            export_3mf(os.path.join(d, "miniatura_2_cores_corpo_e_texto.3mf"), mini)
            resumo[prod]["miniatura_completa"] = info(completa)
        else:
            for name, m in parts:
                m = drop_to_bed(m)
                export_3mf(os.path.join(d, f"{name}.3mf"), [(name, m)])
                resumo[prod][name] = info(m)
            export_3mf(os.path.join(d, "00_MONTADO_visualizacao.3mf"), montado)
        if not a.sem_preview and not os.path.exists(os.path.join(a.previews, f"{prod}.png")):
            render_png(os.path.join(a.previews, f"{prod}.png"), montado, title=prod)
        print("ok", prod)

    with open(os.path.join(a.saida, "resumo_pecas.json"), "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
