// 第5题：Weiler-Atherton多边形裁剪算法

/// 二维点
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }

    pub fn distance_sq(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        dx * dx + dy * dy
    }
}

/// 顶点节点结构
#[derive(Debug, Clone)]
struct Vertex {
    pt: Point,
    t: f64,
    is_intersection: bool,
    is_entering: bool,
    neighbor: Option<usize>,
}

impl Vertex {
    fn new(pt: Point) -> Self {
        Vertex { pt, t: 0.0, is_intersection: false, is_entering: false, neighbor: None }
    }

    fn intersection(pt: Point, t: f64, entering: bool) -> Self {
        Vertex { pt, t, is_intersection: true, is_entering: entering, neighbor: None }
    }
}

/// 交点信息
struct IntersectionInfo {
    pt: Point,
    subj_edge: usize,
    clip_edge: usize,
    t_subj: f64,
    t_clip: f64,
    entering: bool,
}


/// 计算两线段的交点（带公式输出）
fn compute_intersection_verbose(
    a1: Point, a2: Point, b1: Point, b2: Point, verbose: bool
) -> Option<(f64, f64, Point, String)> {
    let dax = a2.x - a1.x;
    let day = a2.y - a1.y;
    let dbx = b2.x - b1.x;
    let dby = b2.y - b1.y;
    let denom = dax * dby - day * dbx;

    if denom.abs() < 1e-10 { return None; }

    let dx = b1.x - a1.x;
    let dy = b1.y - a1.y;
    let ta = (dx * dby - dy * dbx) / denom;
    let tb = (dx * day - dy * dax) / denom;

    const EPS: f64 = 1e-7;
    if ta > EPS && ta < 1.0 - EPS && tb > EPS && tb < 1.0 - EPS {
        let pt = Point::new(a1.x + ta * dax, a1.y + ta * day);
        let formula = format!(
            "t_a = {:.4}, t_b = {:.4}, 交点 = ({:.2}, {:.2})",
            ta, tb, pt.x, pt.y
        );
        Some((ta, tb, pt, formula))
    } else {
        None
    }
}

/// 判断点是否在多边形内部（射线法）
fn point_in_polygon(pt: &Point, polygon: &[Point]) -> bool {
    let mut count = 0;
    let n = polygon.len();
    for i in 0..n {
        let p1 = polygon[i];
        let p2 = polygon[(i + 1) % n];
        if (p1.y <= pt.y && p2.y > pt.y) || (p2.y <= pt.y && p1.y > pt.y) {
            let x = p1.x + (pt.y - p1.y) / (p2.y - p1.y) * (p2.x - p1.x);
            if pt.x < x { count += 1; }
        }
    }
    count % 2 == 1
}

/// 计算多边形有符号面积
pub fn signed_area(polygon: &[Point]) -> f64 {
    let mut area = 0.0;
    let n = polygon.len();
    for i in 0..n {
        let j = (i + 1) % n;
        area += polygon[i].x * polygon[j].y;
        area -= polygon[j].x * polygon[i].y;
    }
    area / 2.0
}


/// Weiler-Atherton多边形裁剪算法（带详细输出）
pub fn weiler_atherton_clip_verbose(
    subject: &[Point], clip: &[Point], verbose: bool
) -> Vec<Vec<Point>> {
    let mut result = Vec::new();
    if subject.len() < 3 || clip.len() < 3 { return result; }

    // 步骤1：计算所有交点
    let mut intersections: Vec<IntersectionInfo> = Vec::new();
    let sn = subject.len();
    let cn = clip.len();

    if verbose {
        println!("\n[1] 求交点");
    }

    for i in 0..sn {
        let s1 = subject[i];
        let s2 = subject[(i + 1) % sn];

        for j in 0..cn {
            let c1 = clip[j];
            let c2 = clip[(j + 1) % cn];

            if let Some((ts, tc, pt, _)) = 
                compute_intersection_verbose(s1, s2, c1, c2, verbose) {
                
                let after_pt = Point::new(
                    s1.x + (ts + 0.001) * (s2.x - s1.x),
                    s1.y + (ts + 0.001) * (s2.y - s1.y),
                );
                let entering = point_in_polygon(&after_pt, clip);

                if verbose {
                    let mark = if entering { "IN" } else { "OUT" };
                    println!("  S{}-S{} ∩ C{}-C{} = ({:.1},{:.1}) [{}]", 
                             i+1, (i+1)%sn+1, j+1, (j+1)%cn+1, pt.x, pt.y, mark);
                }

                intersections.push(IntersectionInfo {
                    pt, subj_edge: i, clip_edge: j,
                    t_subj: ts, t_clip: tc, entering,
                });
            }
        }
    }

    let in_count = intersections.iter().filter(|x| x.entering).count();
    let out_count = intersections.len() - in_count;
    if verbose {
        println!("  共{}个交点 ({}进入, {}离开)", intersections.len(), in_count, out_count);
    }

    // 无交点的特殊情况
    if intersections.is_empty() {
        if verbose { println!("  无交点"); }
        if point_in_polygon(&subject[0], clip) {
            if verbose { println!("  S在C内部"); }
            result.push(subject.to_vec());
        } else if point_in_polygon(&clip[0], subject) {
            if verbose { println!("  C在S内部"); }
            result.push(clip.to_vec());
        } else {
            if verbose { println!("  不相交"); }
        }
        return result;
    }

    // 步骤2-4：构建顶点链表并建立链接
    if verbose {
        println!("\n[2] 构建链表");
    }

    let mut subj_list: Vec<Vertex> = Vec::new();
    for i in 0..sn {
        subj_list.push(Vertex::new(subject[i]));
        let mut edge_inters: Vec<(f64, &IntersectionInfo)> = intersections
            .iter()
            .filter(|inter| inter.subj_edge == i)
            .map(|inter| (inter.t_subj, inter))
            .collect();
        edge_inters.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
        for (t, inter) in edge_inters {
            subj_list.push(Vertex::intersection(inter.pt, t, inter.entering));
        }
    }

    let mut clip_list: Vec<Vertex> = Vec::new();
    for j in 0..cn {
        clip_list.push(Vertex::new(clip[j]));
        let mut edge_inters: Vec<(f64, &IntersectionInfo)> = intersections
            .iter()
            .filter(|inter| inter.clip_edge == j)
            .map(|inter| (inter.t_clip, inter))
            .collect();
        edge_inters.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
        for (t, inter) in edge_inters {
            clip_list.push(Vertex::intersection(inter.pt, t, inter.entering));
        }
    }

    // 建立双向链接
    for i in 0..subj_list.len() {
        if subj_list[i].is_intersection {
            for j in 0..clip_list.len() {
                if clip_list[j].is_intersection {
                    if subj_list[i].pt.distance_sq(&clip_list[j].pt) < 1e-4 {
                        subj_list[i].neighbor = Some(j);
                        clip_list[j].neighbor = Some(i);
                        break;
                    }
                }
            }
        }
    }

    if verbose {
        println!("  S链表: {}节点, C链表: {}节点", subj_list.len(), clip_list.len());
    }

    // 步骤5：从进入点遍历生成结果
    if verbose {
        println!("\n[3] 遍历生成结果");
    }

    let entering_points: Vec<usize> = subj_list
        .iter()
        .enumerate()
        .filter(|(_, v)| v.is_intersection && v.is_entering)
        .map(|(i, _)| i)
        .collect();

    let mut used_as_start: Vec<bool> = vec![false; subj_list.len()];

    for &start_idx in &entering_points {
        if used_as_start[start_idx] { continue; }

        let mut local_visited_s: Vec<bool> = vec![false; subj_list.len()];
        let mut polygon: Vec<Point> = Vec::new();
        let mut current_idx = start_idx;
        let mut on_subject = true;
        let max_iterations = (subj_list.len() + clip_list.len()) * 3;
        let mut first_step = true;

        if verbose {
            print!("  起点({:.0},{:.0}): ", 
                     subj_list[start_idx].pt.x, subj_list[start_idx].pt.y);
        }

        let mut trace: Vec<String> = Vec::new();

        for _ in 0..max_iterations {
            if on_subject {
                if !first_step && current_idx == start_idx { break; }
                first_step = false;

                let v = &subj_list[current_idx];
                polygon.push(v.pt);
                local_visited_s[current_idx] = true;

                if v.is_intersection && !v.is_entering {
                    if let Some(neighbor) = v.neighbor {
                        trace.push(format!("({:.0},{:.0})→C", v.pt.x, v.pt.y));
                        current_idx = (neighbor + 1) % clip_list.len();
                        on_subject = false;
                        continue;
                    }
                }
                current_idx = (current_idx + 1) % subj_list.len();
            } else {
                let v = &clip_list[current_idx];

                if v.is_intersection {
                    if let Some(neighbor) = v.neighbor {
                        if subj_list[neighbor].is_entering {
                            if neighbor == start_idx { break; }
                            trace.push(format!("({:.0},{:.0})→S", v.pt.x, v.pt.y));
                            current_idx = neighbor;
                            on_subject = true;
                            continue;
                        }
                    }
                }
                polygon.push(v.pt);
                current_idx = (current_idx + 1) % clip_list.len();
            }
        }

        if verbose && !trace.is_empty() {
            println!("{}", trace.join(" "));
        }

        if polygon.len() >= 3 {
            for i in 0..subj_list.len() {
                if local_visited_s[i] && subj_list[i].is_intersection && subj_list[i].is_entering {
                    used_as_start[i] = true;
                }
            }

            // 去重
            let mut clean_poly: Vec<Point> = Vec::new();
            for pt in &polygon {
                if clean_poly.is_empty() || pt.distance_sq(clean_poly.last().unwrap()) > 1e-4 {
                    clean_poly.push(*pt);
                }
            }
            if clean_poly.len() > 1 && 
               clean_poly.first().unwrap().distance_sq(clean_poly.last().unwrap()) < 1e-4 {
                clean_poly.pop();
            }

            if clean_poly.len() >= 3 {
                result.push(clean_poly);
            }
        }
    }

    result
}


/// 演示函数
pub fn demo() {
    // 主多边形: 不规则五边形
    let subject = vec![
        Point::new(80.0, 120.0),
        Point::new(220.0, 80.0),
        Point::new(320.0, 180.0),
        Point::new(260.0, 300.0),
        Point::new(100.0, 260.0),
    ];

    // 裁剪多边形: 矩形
    let clip = vec![
        Point::new(120.0, 100.0),
        Point::new(280.0, 100.0),
        Point::new(280.0, 250.0),
        Point::new(120.0, 250.0),
    ];

    println!("主多边形S (五边形):");
    for (i, p) in subject.iter().enumerate() {
        print!("  S{}({},{}) ", i+1, p.x, p.y);
    }
    println!("\n  面积={:.0}", signed_area(&subject).abs());
    
    println!("\n裁剪多边形C (矩形):");
    for (i, p) in clip.iter().enumerate() {
        print!("  C{}({},{}) ", i+1, p.x, p.y);
    }
    println!("\n  面积={:.0}", signed_area(&clip).abs());

    println!("\n--- Weiler-Atherton裁剪 ---");
    let results = weiler_atherton_clip_verbose(&subject, &clip, true);

    println!("\n--- 结果 ---");
    if results.is_empty() {
        println!("无交集");
    } else {
        for (i, poly) in results.iter().enumerate() {
            println!("多边形#{} ({}顶点, 面积={:.1}):", i+1, poly.len(), signed_area(poly).abs());
            for (j, p) in poly.iter().enumerate() {
                print!("  ({:.1},{:.1})", p.x, p.y);
                if (j+1) % 5 == 0 { println!(); }
            }
            if poly.len() % 5 != 0 { println!(); }
        }
    }
}
