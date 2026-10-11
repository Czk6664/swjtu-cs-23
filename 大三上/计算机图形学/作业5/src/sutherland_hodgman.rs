// 第4题：Sutherland-Hodgman多边形裁剪算法

/// 二维点
#[derive(Debug, Clone, Copy)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }
}

/// 矩形裁剪窗口
#[derive(Debug, Clone, Copy)]
pub struct Rect {
    pub xmin: f64,
    pub ymin: f64,
    pub xmax: f64,
    pub ymax: f64,
}

/// 裁剪边类型
#[derive(Clone, Copy, Debug)]
pub enum Edge {
    Left,
    Right,
    Bottom,
    Top,
}

impl Edge {
    fn name(&self) -> &str {
        match self {
            Edge::Left => "左边界",
            Edge::Right => "右边界",
            Edge::Bottom => "下边界",
            Edge::Top => "上边界",
        }
    }
    
    fn condition(&self, rect: &Rect) -> String {
        match self {
            Edge::Left => format!("x >= {}", rect.xmin),
            Edge::Right => format!("x <= {}", rect.xmax),
            Edge::Bottom => format!("y >= {}", rect.ymin),
            Edge::Top => format!("y <= {}", rect.ymax),
        }
    }
}

impl Rect {
    pub fn new(xmin: f64, ymin: f64, xmax: f64, ymax: f64) -> Self {
        Rect { xmin, ymin, xmax, ymax }
    }

    fn is_inside(&self, p: &Point, edge: Edge) -> bool {
        match edge {
            Edge::Left => p.x >= self.xmin,
            Edge::Right => p.x <= self.xmax,
            Edge::Bottom => p.y >= self.ymin,
            Edge::Top => p.y <= self.ymax,
        }
    }


    fn intersect(&self, p1: &Point, p2: &Point, edge: Edge) -> (Point, String) {
        let (x1, y1, x2, y2) = (p1.x, p1.y, p2.x, p2.y);
        match edge {
            Edge::Left => {
                let t = (self.xmin - x1) / (x2 - x1);
                let y = y1 + t * (y2 - y1);
                let formula = format!("t=({}-{})/({}-{})={:.4}, y={}+{:.4}*({}-{})={:.2}", 
                    self.xmin, x1, x2, x1, t, y1, t, y2, y1, y);
                (Point::new(self.xmin, y), formula)
            }
            Edge::Right => {
                let t = (self.xmax - x1) / (x2 - x1);
                let y = y1 + t * (y2 - y1);
                let formula = format!("t=({}-{})/({}-{})={:.4}, y={}+{:.4}*({}-{})={:.2}", 
                    self.xmax, x1, x2, x1, t, y1, t, y2, y1, y);
                (Point::new(self.xmax, y), formula)
            }
            Edge::Bottom => {
                let t = (self.ymin - y1) / (y2 - y1);
                let x = x1 + t * (x2 - x1);
                let formula = format!("t=({}-{})/({}-{})={:.4}, x={}+{:.4}*({}-{})={:.2}", 
                    self.ymin, y1, y2, y1, t, x1, t, x2, x1, x);
                (Point::new(x, self.ymin), formula)
            }
            Edge::Top => {
                let t = (self.ymax - y1) / (y2 - y1);
                let x = x1 + t * (x2 - x1);
                let formula = format!("t=({}-{})/({}-{})={:.4}, x={}+{:.4}*({}-{})={:.2}", 
                    self.ymax, y1, y2, y1, t, x1, t, x2, x1, x);
                (Point::new(x, self.ymax), formula)
            }
        }
    }

    fn clip_edge_verbose(&self, polygon: &[Point], edge: Edge, verbose: bool) -> Vec<Point> {
        let mut output = Vec::new();
        if polygon.is_empty() { return output; }

        if verbose {
            println!("  [{}] {}", edge.name(), edge.condition(self));
        }

        let n = polygon.len();
        for i in 0..n {
            let current = polygon[i];
            let next = polygon[(i + 1) % n];
            let curr_inside = self.is_inside(&current, edge);
            let next_inside = self.is_inside(&next, edge);

            match (curr_inside, next_inside) {
                (true, true) => {
                    output.push(next);
                    if verbose { 
                        println!("    ({:.0},{:.0})->({:.0},{:.0}): 内->内, +终点", 
                                 current.x, current.y, next.x, next.y);
                    }
                }
                (true, false) => {
                    let (inter, _) = self.intersect(&current, &next, edge);
                    output.push(inter);
                    if verbose { 
                        println!("    ({:.0},{:.0})->({:.0},{:.0}): 内->外, +交点({:.1},{:.1})", 
                                 current.x, current.y, next.x, next.y, inter.x, inter.y);
                    }
                }
                (false, true) => {
                    let (inter, _) = self.intersect(&current, &next, edge);
                    output.push(inter);
                    output.push(next);
                    if verbose { 
                        println!("    ({:.0},{:.0})->({:.0},{:.0}): 外->内, +交点({:.1},{:.1})+终点", 
                                 current.x, current.y, next.x, next.y, inter.x, inter.y);
                    }
                }
                (false, false) => {
                    if verbose { 
                        println!("    ({:.0},{:.0})->({:.0},{:.0}): 外->外, 跳过", 
                                 current.x, current.y, next.x, next.y);
                    }
                }
            }
        }
        if verbose {
            println!("    => {}个顶点", output.len());
        }
        output
    }
}


/// Sutherland-Hodgman多边形裁剪（带详细输出）
pub fn sutherland_hodgman_clip_verbose(polygon: &[Point], rect: &Rect, verbose: bool) -> Vec<Point> {
    if polygon.len() < 3 {
        return Vec::new();
    }

    let mut result = polygon.to_vec();
    let edges = [Edge::Left, Edge::Right, Edge::Bottom, Edge::Top];

    for edge in edges.iter() {
        if verbose {
            println!();
        }
        
        result = rect.clip_edge_verbose(&result, *edge, verbose);

        if result.is_empty() {
            break;
        }
    }

    result
}

/// 计算多边形面积
pub fn polygon_area(polygon: &[Point]) -> f64 {
    if polygon.len() < 3 { return 0.0; }
    let mut area = 0.0;
    let n = polygon.len();
    for i in 0..n {
        let j = (i + 1) % n;
        area += polygon[i].x * polygon[j].y;
        area -= polygon[j].x * polygon[i].y;
    }
    (area / 2.0).abs()
}

/// 演示函数
pub fn demo() {
    // 六边形测试
    let rect = Rect::new(80.0, 80.0, 280.0, 220.0);
    let polygon = vec![
        Point::new(30.0, 120.0),
        Point::new(150.0, 30.0),
        Point::new(320.0, 100.0),
        Point::new(300.0, 250.0),
        Point::new(180.0, 280.0),
        Point::new(60.0, 200.0),
    ];

    println!("窗口: x∈[{},{}], y∈[{},{}]", rect.xmin, rect.xmax, rect.ymin, rect.ymax);
    println!("原多边形 ({}个顶点):", polygon.len());
    for (i, p) in polygon.iter().enumerate() {
        print!("  V{}({},{})", i+1, p.x, p.y);
        if i < polygon.len()-1 { print!(" ->"); }
    }
    println!("\n面积 = {:.1}\n", polygon_area(&polygon));

    println!("=== 逐边裁剪过程 ===");
    let clipped = sutherland_hodgman_clip_verbose(&polygon, &rect, true);

    println!("\n=== 裁剪完成 ===");
    if clipped.is_empty() {
        println!("结果: 空 (多边形在窗口外)");
    } else {
        println!("结果多边形 ({}个顶点):", clipped.len());
        for (i, p) in clipped.iter().enumerate() {
            print!("  ({:.1},{:.1})", p.x, p.y);
            if (i+1) % 4 == 0 { println!(); }
        }
        if clipped.len() % 4 != 0 { println!(); }
        println!("面积 = {:.1}", polygon_area(&clipped));
    }
}
