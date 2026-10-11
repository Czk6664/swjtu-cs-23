// 定义点结构
#[derive(Clone, Copy, Debug)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }
}

/// 计算四阶Bezier曲线上的所有点
pub fn bezier_curve_order4(control_points: &[Point; 4], num_points: usize) -> Vec<Point> {
    let mut curve_points = Vec::with_capacity(num_points);
    
    for i in 0..num_points {
        let t = i as f64 / (num_points - 1) as f64;
        
        let b0 = (1.0 - t).powi(3);
        let b1 = 3.0 * t * (1.0 - t).powi(2);
        let b2 = 3.0 * t.powi(2) * (1.0 - t);
        let b3 = t.powi(3);
        
        let x = b0 * control_points[0].x
              + b1 * control_points[1].x
              + b2 * control_points[2].x
              + b3 * control_points[3].x;
              
        let y = b0 * control_points[0].y
              + b1 * control_points[1].y
              + b2 * control_points[2].y
              + b3 * control_points[3].y;
        
        curve_points.push(Point::new(x, y));
    }
    
    curve_points
}

/// 使用矩阵形式计算四阶Bezier曲线
pub fn bezier_curve_order4_matrix(control_points: &[Point; 4], num_points: usize) -> Vec<Point> {
    let mut curve_points = Vec::with_capacity(num_points);
    
    let matrix: [[f64; 4]; 4] = [
        [ 1.0,  0.0,  0.0,  0.0],
        [-3.0,  3.0,  0.0,  0.0],
        [ 3.0, -6.0,  3.0,  0.0],
        [-1.0,  3.0, -3.0,  1.0],
    ];
    
    for i in 0..num_points {
        let t = i as f64 / (num_points - 1) as f64;
        let t_vec = [1.0, t, t.powi(2), t.powi(3)];
        
        let mut temp = [0.0; 4];
        for j in 0..4 {
            for k in 0..4 {
                temp[j] += t_vec[k] * matrix[k][j];
            }
        }
        
        let mut x = 0.0;
        let mut y = 0.0;
        for j in 0..4 {
            x += temp[j] * control_points[j].x;
            y += temp[j] * control_points[j].y;
        }
        
        curve_points.push(Point::new(x, y));
    }
    
    curve_points
}

/// 计算三阶B样条曲线上的所有点
pub fn bspline_curve_order3(control_points: &[Point], points_per_segment: usize) -> Vec<Point> {
    if control_points.len() < 3 {
        panic!("至少需要3个控制点来生成三阶B样条曲线");
    }
    
    let num_segments = control_points.len() - 2;
    let mut curve_points = Vec::new();
    
    for seg in 0..num_segments {
        let p0 = control_points[seg];
        let p1 = control_points[seg + 1];
        let p2 = control_points[seg + 2];
        
        for i in 0..points_per_segment {
            if seg > 0 && i == 0 {
                continue;
            }
            
            let t = i as f64 / (points_per_segment - 1) as f64;
            
            let n0 = (1.0 - t).powi(2) / 2.0;
            let n1 = (-2.0 * t.powi(2) + 2.0 * t + 1.0) / 2.0;
            let n2 = t.powi(2) / 2.0;
            
            let x = n0 * p0.x + n1 * p1.x + n2 * p2.x;
            let y = n0 * p0.y + n1 * p1.y + n2 * p2.y;
            
            curve_points.push(Point::new(x, y));
        }
    }
    
    curve_points
}

/// 使用矩阵形式计算三阶B样条曲线
pub fn bspline_curve_order3_matrix(control_points: &[Point], points_per_segment: usize) -> Vec<Point> {
    if control_points.len() < 3 {
        panic!("至少需要3个控制点来生成三阶B样条曲线");
    }
    
    let num_segments = control_points.len() - 2;
    let mut curve_points = Vec::new();
    
    let matrix: [[f64; 3]; 3] = [
        [ 1.0/2.0,  1.0/2.0,  0.0],
        [-2.0/2.0,  2.0/2.0,  0.0],
        [ 1.0/2.0, -2.0/2.0,  1.0/2.0],
    ];
    
    for seg in 0..num_segments {
        let p = [
            control_points[seg],
            control_points[seg + 1],
            control_points[seg + 2],
        ];
        
        for i in 0..points_per_segment {
            if seg > 0 && i == 0 {
                continue;
            }
            
            let t = i as f64 / (points_per_segment - 1) as f64;
            let t_vec = [1.0, t, t.powi(2)];
            
            let mut temp = [0.0; 3];
            for j in 0..3 {
                for k in 0..3 {
                    temp[j] += t_vec[k] * matrix[k][j];
                }
            }
            
            let mut x = 0.0;
            let mut y = 0.0;
            for j in 0..3 {
                x += temp[j] * p[j].x;
                y += temp[j] * p[j].y;
            }
            
            curve_points.push(Point::new(x, y));
        }
    }
    
    curve_points
}

fn main() {
    println!("=== 四阶Bezier曲线测试 ===\n");
    
    let bezier_control = [
        Point::new(0.0, 0.0),
        Point::new(1.0, 2.0),
        Point::new(3.0, 2.0),
        Point::new(4.0, 0.0),
    ];
    
    println!("控制点:");
    for (i, p) in bezier_control.iter().enumerate() {
        println!("  P{}: ({:.2}, {:.2})", i, p.x, p.y);
    }
    
    let bezier_points = bezier_curve_order4(&bezier_control, 10);
    println!("\n生成的Bezier曲线点 (10个采样点):");
    for (i, p) in bezier_points.iter().enumerate() {
        println!("  点{}: ({:.4}, {:.4})", i, p.x, p.y);
    }
    
    // 验证端点
    println!("\n端点验证:");
    println!("  起点: ({:.4}, {:.4}) - 应为 (0.0, 0.0)", bezier_points[0].x, bezier_points[0].y);
    println!("  终点: ({:.4}, {:.4}) - 应为 (4.0, 0.0)", bezier_points[9].x, bezier_points[9].y);
    
    // 测试矩阵方法
    let bezier_points_matrix = bezier_curve_order4_matrix(&bezier_control, 10);
    println!("\n矩阵方法验证 (前3个点):");
    for i in 0..3 {
        let diff_x = (bezier_points[i].x - bezier_points_matrix[i].x).abs();
        let diff_y = (bezier_points[i].y - bezier_points_matrix[i].y).abs();
        println!("  点{}: 差异 = ({:.2e}, {:.2e})", i, diff_x, diff_y);
    }
    
    println!("\n=== 三阶B样条曲线测试 ===\n");
    
    let bspline_control = vec![
        Point::new(0.0, 0.0),
        Point::new(1.0, 2.0),
        Point::new(3.0, 2.0),
        Point::new(4.0, 0.0),
    ];
    
    println!("控制点:");
    for (i, p) in bspline_control.iter().enumerate() {
        println!("  P{}: ({:.2}, {:.2})", i, p.x, p.y);
    }
    
    let bspline_points = bspline_curve_order3(&bspline_control, 10);
    println!("\n生成的B样条曲线点:");
    println!("  总点数: {}", bspline_points.len());
    println!("  前5个点:");
    for (i, p) in bspline_points.iter().take(5).enumerate() {
        println!("    点{}: ({:.4}, {:.4})", i, p.x, p.y);
    }
    
    // 测试矩阵方法
    let bspline_points_matrix = bspline_curve_order3_matrix(&bspline_control, 10);
    println!("\n矩阵方法验证:");
    println!("  点数匹配: {}", bspline_points.len() == bspline_points_matrix.len());
    let mut max_diff: f64 = 0.0;
    for i in 0..bspline_points.len() {
        let diff_x = (bspline_points[i].x - bspline_points_matrix[i].x).abs();
        let diff_y = (bspline_points[i].y - bspline_points_matrix[i].y).abs();
        max_diff = max_diff.max(diff_x).max(diff_y);
    }
    println!("  最大差异: {:.2e}", max_diff);
    
    println!("\n✓ 所有测试完成!");
}
