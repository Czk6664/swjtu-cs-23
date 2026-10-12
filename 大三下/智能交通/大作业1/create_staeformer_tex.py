import numpy as np

def main():
    np.random.seed(42)
    T, N, D = 4, 4, 4
    CW, RH = 1.2, 0.7

    # ===== Data =====
    x_node0 = np.array([[45],[48],[52],[55]], dtype=float)
    x_norm = (x_node0 - 50) / 15.0
    W_p = np.random.randn(1, D) * 0.5
    X_proj = x_norm @ W_p
    E_time = np.random.randn(T, D) * 0.4
    E_node = np.tile(np.random.randn(1, D) * 0.3, (T, 1))
    E_adp = np.random.randn(T, D) * 0.4
    X_emb = X_proj + E_time + E_node + E_adp

    W_Q, W_K, W_V = [np.random.randn(D, D) * 0.5 for _ in range(3)]
    Q, K, V = X_emb @ W_Q, X_emb @ W_K, X_emb @ W_V
    Score = Q @ K.T
    def softmax(x):
        e = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e / e.sum(axis=-1, keepdims=True)
    A_temp = softmax(Score / 2.0)
    H_temp = A_temp @ V

    X_sp = np.random.randn(N, D) * 0.6
    A_spat = softmax(np.random.randn(N, N) * 1.2)
    H_spat = A_spat @ X_sp
    W1, W2 = np.random.randn(D, 2*D) * 0.5, np.random.randn(2*D, D) * 0.5
    H_ff = np.maximum(0, H_spat @ W1) @ W2
    W_out = np.random.randn(D, 1) * 1.5
    Y_pred = H_ff @ W_out + 50

    # ===== Helpers =====
    def hf(v, lo, hi):
        p = 30 if abs(hi-lo)<1e-8 else int(8+((v-lo)/(hi-lo))*80)
        return f"datag!{p}!white", ("white" if p > 48 else "black")

    def mat(nm, data, ax, ay, rl=None, cl=None):
        r, c = data.shape; lo, hi = data.min(), data.max(); L = []
        for j in range(c):
            lb = cl[j] if cl else f"${j}$"
            L.append(f"\\node[colhd] at ({ax+j*CW:.2f},{ay:.2f}) {{{lb}}};")
        for i in range(r):
            lb = rl[i] if rl else f"${i}$"
            L.append(f"\\node[rowhd] at ({ax-CW:.2f},{ay+(i+1)*RH:.2f}) {{{lb}}};")
        for i in range(r):
            for j in range(c):
                v = data[i,j]; fc, tc = hf(v, lo, hi)
                L.append(f"\\node[dcell,fill={fc},text={tc}] ({nm}{i}{j}) at ({ax+j*CW:.2f},{ay+(i+1)*RH:.2f}) {{{v:.2f}}};")
        lx, rx = ax-CW*1.5, ax+(c-0.5)*CW
        ty, by_ = ay-RH*0.5, ay+(r+0.5)*RH
        L.append(f"\\draw[frame] ({lx:.2f},{ty:.2f}) rectangle ({rx:.2f},{by_:.2f});")
        return "\n".join(L)

    def mt(text, ax, ay, nc):
        cx = ax + (nc-1)*CW/2
        return f"\\node[matlbl] at ({cx:.2f},{ay-RH-0.15:.2f}) {{{text}}};"

    re = lambda ax, nc: ax + (nc-0.5)*CW
    le = lambda ax: ax - CW*1.5
    cy = lambda ay, nr: ay + (nr+1)*RH/2
    cx_f = lambda ax, nc: ax + (nc-1)*CW/2

    def ha(x1, x2, y, lb=""):
        s = f"\\draw[arr] ({x1:.2f},{y:.2f}) -- ({x2:.2f},{y:.2f});\n"
        if lb: s += f"\\node[albl] at ({(x1+x2)/2:.2f},{y-0.35:.2f}) {{{lb}}};"
        return s

    def va(x, y1, y2, lb=""):
        s = f"\\draw[arr] ({x:.2f},{y1:.2f}) -- ({x:.2f},{y2:.2f});\n"
        if lb: s += f"\\node[albl,anchor=west] at ({x+0.3:.2f},{(y1+y2)/2:.2f}) {{{lb}}};"
        return s

    # ===== TeX =====
    tex = r"""\documentclass[10pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{xeCJK}
\setCJKmainfont{Microsoft YaHei}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\geometry{a3paper, margin=1.5cm, landscape}
\usepackage{tikz}
\usetikzlibrary{arrows.meta}
\usepackage{xcolor}
\pagestyle{empty}

\definecolor{datag}{HTML}{2E7D32}
\definecolor{headbg}{HTML}{5D6D7E}
\definecolor{titcol}{HTML}{1A1A2E}
\definecolor{arrcol}{HTML}{4A4A4A}
\definecolor{fmlcol}{HTML}{800020}
\definecolor{frmcol}{HTML}{AAAAAA}

\tikzset{
  colhd/.style={rectangle,draw=gray!30,fill=headbg,text=white,minimum width=1.15cm,minimum height=0.58cm,font=\tiny\bfseries,align=center},
  rowhd/.style={rectangle,draw=gray!30,fill=headbg,text=white,minimum width=1.15cm,minimum height=0.58cm,font=\tiny\bfseries,align=center},
  dcell/.style={rectangle,draw=gray!25,minimum width=1.15cm,minimum height=0.58cm,font=\tiny,align=center},
  frame/.style={thick,frmcol,rounded corners=1pt},
  matlbl/.style={font=\footnotesize\bfseries,text=titcol,align=center},
  stitle/.style={font=\Large\bfseries,text=titcol},
  sdesc/.style={font=\small,text=black!55,align=center},
  arr/.style={-{Stealth[scale=0.8]},semithick,arrcol},
  albl/.style={font=\scriptsize,text=arrcol,align=center,fill=white,inner sep=1pt,rounded corners=1pt},
  fml/.style={font=\small\itshape,text=fmlcol,align=center},
  opn/.style={font=\large\bfseries,text=arrcol}
}
\begin{document}
"""

    # ========== PAGE 1 ==========
    tex += "\\begin{center}{\\Large\\bfseries\\textcolor{titcol}{STAEformer 计算流程逐层详解}}\\\\[2pt]\n"
    tex += "{\\small\\textcolor{black!45}{数据格子统一绿色热力图：浅绿 = 小值，深绿 = 大值}}\\end{center}\\vspace{1mm}\n"
    tex += "\\begin{tikzpicture}[x=1cm,y=-1cm]\n"
    tex += "\\node[stitle] at (19,0) {Step 1\\quad 时空自适应嵌入层 (Embedding Layer)};\n"
    tex += "\\node[sdesc] at (19,0.7) {原始流量经线性投影升维，叠加时间·空间·自适应嵌入};\n"
    tex += "\\node[fml] at (10,1.5) {$X_{proj}=\\mathrm{Norm}(X_{in})\\cdot W_p$};\n"

    # Row 1: X_in -> W_p -> X_proj
    a1x, a1y = 2.5, 3
    tex += mt("$X_{in}$", a1x, a1y, 1) + "\n" + mat("xi", x_node0, a1x, a1y, rl=[f"$t_{{{i}}}$" for i in range(T)], cl=["flow"]) + "\n"
    tex += ha(re(a1x,1)+0.3, 7.3, cy(a1y,T), "$\\times W_p$") + "\n"

    a2x, a2y = 8.5, 4
    tex += mt("$W_p\\;(1{\\times}4)$", a2x, a2y, D) + "\n" + mat("wp", W_p, a2x, a2y, rl=["$c$"], cl=[f"$d_{{{j}}}$" for j in range(D)]) + "\n"
    tex += ha(re(a2x,D)+0.3, 15.3, cy(a2y,1), "=") + "\n"

    a3x, a3y = 16.5, 3
    tex += mt("$X_{proj}\\;(T{\\times}D)$", a3x, a3y, D) + "\n" + mat("xp", X_proj, a3x, a3y, rl=[f"$t_{{{i}}}$" for i in range(T)], cl=[f"$d_{{{j}}}$" for j in range(D)]) + "\n"

    # Row 2: Embedding fusion
    tex += "\\node[fml] at (19,8.5) {$X_{emb}=X_{proj}+E_{time}+E_{node}+E_{adp}$};\n"
    by = 10
    mw = (D+1)*CW; og = 1.6
    tw = 5*mw + 4*og; sx = (39.6-tw)/2 + CW*1.5
    mats = [("p2",X_proj,"$X_{proj}$"),("et",E_time,"$E_{time}$"),("en",E_node,"$E_{node}$"),("ea",E_adp,"$E_{adp}$"),("xe",X_emb,"$X_{emb}$")]
    ops = ["+","+","+","="]
    for idx,(nm,dt,lb) in enumerate(mats):
        px = sx + idx*(mw+og)
        tex += mt(lb, px, by, D) + "\n" + mat(nm, dt, px, by, rl=[f"$t_{{{i}}}$" for i in range(T)]) + "\n"
        if idx < 4:
            ox = re(px,D) + og/2
            tex += f"\\node[opn] at ({ox:.2f},{cy(by,T):.2f}) {{{ops[idx]}}};\n"
    tex += "\\end{tikzpicture}\n\\newpage\n\n"

    # ========== PAGE 2 ==========
    tex += "\\begin{tikzpicture}[x=1cm,y=-1cm]\n"
    tex += "\\node[stitle] at (19,0) {Step 2\\quad 时间自注意力 (Temporal Self-Attention)};\n"
    tex += "\\node[sdesc] at (19,0.7) {沿时间轴计算 Q/K/V 并得到注意力权重，捕获时序依赖};\n"
    tex += "\\node[fml] at (19,1.4) {$\\mathrm{Attn}(Q,K,V)=\\mathrm{Softmax}\\!\\left(QK^\\top/\\sqrt{d_k}\\right)V$};\n"

    ix, iy = 2, 6
    tex += mt("$X_{emb}$", ix, iy, D) + "\n" + mat("x2", X_emb, ix, iy, rl=[f"$t_{{{i}}}$" for i in range(T)], cl=[f"$d_{{{j}}}$" for j in range(D)]) + "\n"

    qx, qy = 10, 3
    tex += mt("$Q=X W_Q$", qx, qy, D) + "\n" + mat("qq", Q, qx, qy, rl=[f"$t_{{{i}}}$" for i in range(T)]) + "\n"
    tex += ha(re(ix,D)+0.3, le(qx)-0.3, cy(qy,T), "$\\times W_Q$") + "\n"

    ky_ = qy + (T+1)*RH + 1.5
    tex += mt("$K=X W_K$", qx, ky_, D) + "\n" + mat("kk", K, qx, ky_, rl=[f"$t_{{{i}}}$" for i in range(T)]) + "\n"

    vy_ = ky_ + (T+1)*RH + 1.5
    tex += mt("$V=X W_V$", qx, vy_, D) + "\n" + mat("vv", V, qx, vy_, rl=[f"$t_{{{i}}}$" for i in range(T)]) + "\n"

    scx, scy = 20, 3
    tex += mt("$S=QK^\\top$", scx, scy, T) + "\n" + mat("sc", Score, scx, scy, rl=[f"$q_{{{i}}}$" for i in range(T)], cl=[f"$k_{{{j}}}$" for j in range(T)]) + "\n"
    tex += ha(re(qx,D)+0.3, le(scx)-0.3, cy(scy,T), "$Q{\\times}K^\\top$") + "\n"

    ay_ = scy + (T+1)*RH + 1.8
    tex += mt("$A_{temp}=\\mathrm{Softmax}(S/\\sqrt{d})$", scx, ay_, T) + "\n" + mat("at", A_temp, scx, ay_, rl=[f"$t_{{{i}}}$" for i in range(T)], cl=[f"$t_{{{j}}}$" for j in range(T)]) + "\n"
    tex += va(cx_f(scx,T), scy+(T+0.5)*RH+0.3, ay_-RH*0.5-0.3, "Softmax") + "\n"

    hx, hy = 30, ay_
    tex += mt("$H_{temp}=A_{temp}V$", hx, hy, D) + "\n" + mat("ht", H_temp, hx, hy, rl=[f"$t_{{{i}}}$" for i in range(T)], cl=[f"$d_{{{j}}}$" for j in range(D)]) + "\n"
    tex += ha(re(scx,T)+0.3, le(hx)-0.3, cy(hy,T), "$A{\\times}V$") + "\n"
    tex += "\\end{tikzpicture}\n\\newpage\n\n"

    # ========== PAGE 3 ==========
    tex += "\\begin{tikzpicture}[x=1cm,y=-1cm]\n"
    tex += "\\node[stitle] at (19,0) {Step 3\\quad 空间注意力与回归 (Spatial Attention + FFN + Regression)};\n"
    tex += "\\node[sdesc] at (19,0.7) {沿空间维度 (Node) 聚合节点特征，经前馈网络与线性层完成预测};\n"

    s1x, s1y = 2, 3
    tex += mt("$H_{temp}[t_0]$", s1x, s1y, D) + "\n" + mat("si", X_sp, s1x, s1y, rl=[f"$n_{{{i}}}$" for i in range(N)], cl=[f"$d_{{{j}}}$" for j in range(D)]) + "\n"

    s2x = 10
    tex += mt("$A_{spat}$", s2x, s1y, N) + "\n" + mat("as", A_spat, s2x, s1y, rl=[f"$n_{{{i}}}$" for i in range(N)], cl=[f"$n_{{{j}}}$" for j in range(N)]) + "\n"
    tex += ha(re(s1x,D)+0.3, le(s2x)-0.3, cy(s1y,N), "空间 QKV") + "\n"

    s3x = 18
    tex += mt("$H_{spat}$", s3x, s1y, D) + "\n" + mat("hs", H_spat, s3x, s1y, rl=[f"$n_{{{i}}}$" for i in range(N)]) + "\n"
    tex += ha(re(s2x,N)+0.3, le(s3x)-0.3, cy(s1y,N), "$A_{spat}{\\times}V_s$") + "\n"

    fy = s1y + (N+1)*RH + 2.5
    tex += "\\node[fml] at (20,{fy-1.2:.2f}) {{FFN: $H_{{ff}}=\\mathrm{{ReLU}}(H_{{spat}}W_1)W_2$}};".replace("{fy-1.2:.2f}",f"{fy-1.2:.2f}")
    s4x = 18
    tex += mt("$H_{ff}$", s4x, fy, D) + "\n" + mat("hf", H_ff, s4x, fy, rl=[f"$n_{{{i}}}$" for i in range(N)]) + "\n"
    tex += va(cx_f(s3x,D), s1y+(N+0.5)*RH+0.3, fy-RH*0.5-0.3, "FFN") + "\n"

    s5x = 10
    tex += mt("$\\hat{Y}=H_{ff}W_{out}$", s5x, fy, 1) + "\n" + mat("pr", Y_pred, s5x, fy, rl=[f"$n_{{{i}}}$" for i in range(N)], cl=["$\\hat{y}$"]) + "\n"
    tex += ha(le(s4x)-0.3, re(s5x,1)+0.3, cy(fy,N), "$\\times W_{out}$") + "\n"

    tex += "\\end{tikzpicture}\n\\end{document}\n"

    out = r"D:\大三下\智能交通\Steaformer_Excel_Style.tex"
    with open(out, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"OK: {out}")

if __name__ == "__main__":
    main()
