// 第3题：中点分割裁剪算法

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

// 区域编码常量
const LEFT: u8 = 1;   // 0001
const RIGHT: u8 = 2;  // 0010
const BOTTOM: u8 = 4; // 0100
const TOP: u8 = 8;    // 1000

impl Rect {
    pub fn new(xmin: f64, ymin: f64, xmax: f64, ymax: f64) -> Self {
        Rect { xmin, ymin, xmax, ymax }
    }

    /// 计算点的区域编码
    pub fn compute_code(&self, p: &Point) -> u8 {
        let mut code = 0u8;
        if p.x < self.xmin { code |= LEFT; }
        if p.x > self.xmax { code |= RIGHT; }
        if p.y < self.ymin { code |= BOTTOM; }
        if p.y > self.ymax { code |= TOP; }
        code
    }

    /// 获取编码的字符串表示
    pub fn code_to_string(&self, code: u8) -> String {
        format!("{:04b}", code)
    }
}


/// 二分查找边界交点（带详细输出）
fn find_boundary_verbose(inside: Point, outside: Point, rect: &Rect, verbose: bool) -> Point {
    let mut p_in = inside;
    let mut p_out = outside;
    const EPS: f64 = 1e-6;
    let mut iter = 0;

    if verbose {
        println!("    二分查找边界交点:");
        println!("      初始: P_in=({:.2},{:.2}), P_out=({:.2},{:.2})", 
                 p_in.x, p_in.y, p_out.x, p_out.y);
    }

    while (p_in.x - p_out.x).abs() > EPS || (p_in.y - p_out.y).abs() > EPS {
        let mid = Point::new(
            (p_in.x + p_out.x) / 2.0,
            (p_in.y + p_out.y) / 2.0,
        );
        iter += 1;
        
        if rect.compute_code(&mid) == 0 {
            if verbose && iter <= 3 {
                println!("      第{}次: mid=({:.4},{:.4}) 在窗口内, P_in=mid", 
                         iter, mid.x, mid.y);
            }
            p_in = mid;
        } else {
            if verbose && iter <= 3 {
                println!("      第{}次: mid=({:.4},{:.4}) 在窗口外, P_out=mid", 
                         iter, mid.x, mid.y);
            }
            p_out = mid;
        }
    }
    
    if verbose {
        println!("      经过{}次迭代, 交点=({:.6},{:.6})", iter, p_in.x, p_in.y);
    }
    p_in
}

/// 中点分割裁剪算法
pub fn midpoint_clip(p1: Point, p2: Point, rect: &Rect) -> Option<(Point, Point)> {
    midpoint_clip_internal(p1, p2, rect, false)
}

fn midpoint_clip_internal(p1: Point, p2: Point, rect: &Rect, verbose: bool) -> Option<(Point, Point)> {
    let code1 = rect.compute_code(&p1);
    let code2 = rect.compute_code(&p2);

    if code1 == 0 && code2 == 0 {
        return Some((p1, p2));
    }
    
    if (code1 & code2) != 0 {
        return None;
    }

    if code1 == 0 {
        let boundary = find_boundary_verbose(p1, p2, rect, verbose);
        Some((p1, boundary))
    } else if code2 == 0 {
        let boundary = find_boundary_verbose(p2, p1, rect, verbose);
        Some((boundary, p2))
    } else {
        let mid = Point::new((p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0);
        let left = midpoint_clip_internal(p1, mid, rect, false);
        let right = midpoint_clip_internal(mid, p2, rect, false);
        match (left, right) {
            (Some((a, _)), Some((_, d))) => Some((a, d)),
            (Some(seg), None) | (None, Some(seg)) => Some(seg),
            (None, None) => None,
        }
    }
}


/// 演示函数
pub fn demo() {
    // 使用不同的测试数据
    let rect = Rect::new(50.0, 50.0, 250.0, 200.0);
    let p1 = Point::new(20.0, 80.0);
    let p2 = Point::new(300.0, 180.0);

    println!("裁剪窗口: [{}, {}] x [{}, {}]", rect.xmin, rect.xmax, rect.ymin, rect.ymax);
    println!("待裁剪线段: ({}, {}) -> ({}, {})", p1.x, p1.y, p2.x, p2.y);
    println!();

    // 区域编码
    let code1 = rect.compute_code(&p1);
    let code2 = rect.compute_code(&p2);
    
    println!("Step1: 区域编码 (TBRL格式)");
    println!("  P1: x={}<{}? {} | x={}>{} ? {} | y={}<{}? {} | y={}>{}? {}", 
             p1.x, rect.xmin, if p1.x < rect.xmin {1} else {0},
             p1.x, rect.xmax, if p1.x > rect.xmax {1} else {0},
             p1.y, rect.ymin, if p1.y < rect.ymin {1} else {0},
             p1.y, rect.ymax, if p1.y > rect.ymax {1} else {0});
    println!("      => code1 = {:04b}", code1);
    
    println!("  P2: x={}<{}? {} | x={}>{} ? {} | y={}<{}? {} | y={}>{}? {}", 
             p2.x, rect.xmin, if p2.x < rect.xmin {1} else {0},
             p2.x, rect.xmax, if p2.x > rect.xmax {1} else {0},
             p2.y, rect.ymin, if p2.y < rect.ymin {1} else {0},
             p2.y, rect.ymax, if p2.y > rect.ymax {1} else {0});
    println!("      => code2 = {:04b}", code2);
    println!();

    println!("Step2: 快速判断");
    println!("  code1 & code2 = {:04b} & {:04b} = {:04b}", code1, code2, code1 & code2);
    if code1 == 0 && code2 == 0 {
        println!("  两端点都在窗口内，直接接受");
    } else if (code1 & code2) != 0 {
        println!("  线段必在窗口外，直接拒绝");
    } else {
        println!("  需要计算交点");
    }
    println!();

    // 参数方程
    let dx = p2.x - p1.x;
    let dy = p2.y - p1.y;
    
    println!("Step3: 求交点");
    println!("  参数式: x = {} + {}t, y = {} + {}t", p1.x, dx, p1.y, dy);
    
    // 左边界
    let t_left = (rect.xmin - p1.x) / dx;
    let y_at_left = p1.y + t_left * dy;
    println!("  左边界x={}: t=({}-{})/{} = {:.3}", rect.xmin, rect.xmin, p1.x, dx, t_left);
    println!("              y = {} + {:.3}*{} = {:.2}", p1.y, t_left, dy, y_at_left);
    
    // 右边界
    let t_right = (rect.xmax - p1.x) / dx;
    let y_at_right = p1.y + t_right * dy;
    println!("  右边界x={}: t=({}-{})/{} = {:.3}", rect.xmax, rect.xmax, p1.x, dx, t_right);
    println!("              y = {} + {:.3}*{} = {:.2}", p1.y, t_right, dy, y_at_right);
    println!();

    println!("Step4: 结果");
    match midpoint_clip(p1, p2, &rect) {
        Some((a, b)) => {
            println!("  可见部分: ({:.1}, {:.1}) -> ({:.1}, {:.1})", a.x, a.y, b.x, b.y);
        }
        None => {
            println!("  线段不可见");
        }
    }
}
