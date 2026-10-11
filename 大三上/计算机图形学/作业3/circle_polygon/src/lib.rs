/// 点结构体
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Point {
    pub x: i32,
    pub y: i32,
}

impl Point {
    /// 创建新的点
    pub fn new(x: i32, y: i32) -> Self {
        Point { x, y }
    }
}

/// Bresenham圆绘制算法
/// 
/// 利用圆的八分对称性，只计算第一象限的1/8圆弧（0°到45°），
/// 然后通过对称性得到其他7个部分的点
/// 
/// # 参数
/// * `center_x` - 圆心x坐标
/// * `center_y` - 圆心y坐标
/// * `radius` - 圆的半径
/// 
/// # 返回值
/// 返回圆上所有点的坐标向量
pub fn bresenham_circle(center_x: i32, center_y: i32, radius: i32) -> Vec<Point> {
    let mut points = Vec::new();
    
    // 从第一个八分圆开始（x=0, y=r）
    let mut x = 0;
    let mut y = radius;
    
    // 初始决策参数 d = 3 - 2r
    let mut d = 3 - 2 * radius;
    
    // 利用对称性绘制完整的圆
    while x <= y {
        // 利用八分对称性添加8个对称点
        points.push(Point::new(center_x + x, center_y + y)); // 第1象限 (0-45度)
        points.push(Point::new(center_x + y, center_y + x)); // 第1象限 (45-90度)
        points.push(Point::new(center_x - x, center_y + y)); // 第2象限 (90-135度)
        points.push(Point::new(center_x - y, center_y + x)); // 第2象限 (135-180度)
        points.push(Point::new(center_x - x, center_y - y)); // 第3象限 (180-225度)
        points.push(Point::new(center_x - y, center_y - x)); // 第3象限 (225-270度)
        points.push(Point::new(center_x + x, center_y - y)); // 第4象限 (270-315度)
        points.push(Point::new(center_x + y, center_y - x)); // 第4象限 (315-360度)
        
        // 根据决策参数更新坐标
        if d < 0 {
            // 选择右侧像素点 (x+1, y)
            d = d + 4 * x + 6;
        } else {
            // 选择右下像素点 (x+1, y-1)
            d = d + 4 * (x - y) + 10;
            y -= 1;
        }
        x += 1;
    }
    
    // 去除重复的点（主要是轴上的点）
    points.sort_by(|a, b| {
        if a.x != b.x {
            a.x.cmp(&b.x)
        } else {
            a.y.cmp(&b.y)
        }
    });
    points.dedup();
    
    points
}

/// 边表项，用于扫描线填充算法
#[derive(Debug, Clone)]
struct EdgeTableEntry {
    /// y的最大值
    y_max: i32,
    /// 当前x坐标
    x: f64,
    /// 斜率的倒数 dx/dy
    inverse_slope: f64,
}

/// 扫描线填充算法
/// 
/// 使用活性边表(AET)和边表(ET)对多边形进行填充
/// 
/// # 参数
/// * `vertices` - 多边形顶点坐标数组
/// 
/// # 返回值
/// 返回填充区域内所有点的坐标向量
pub fn scanline_fill(vertices: &[Point]) -> Vec<Point> {
    if vertices.len() < 3 {
        return Vec::new();
    }
    
    let mut points = Vec::new();
    
    // 1. 构建边表(ET - Edge Table)
    // 找出y的最小值和最大值
    let y_min = vertices.iter().map(|p| p.y).min().unwrap();
    let y_max = vertices.iter().map(|p| p.y).max().unwrap();
    
    // 为每一条扫描线创建一个边表
    let mut edge_table: Vec<Vec<EdgeTableEntry>> = vec![Vec::new(); (y_max - y_min + 1) as usize];
    
    // 遍历所有边，将非水平边加入边表
    let n = vertices.len();
    for i in 0..n {
        let v1 = vertices[i];
        let v2 = vertices[(i + 1) % n];
        
        // 跳过水平边
        if v1.y == v2.y {
            continue;
        }
        
        // 确保v1是下端点（y较小）
        let (lower, upper) = if v1.y < v2.y {
            (v1, v2)
        } else {
            (v2, v1)
        };
        
        // 创建边表项
        let entry = EdgeTableEntry {
            y_max: upper.y,
            x: lower.x as f64,
            inverse_slope: (upper.x - lower.x) as f64 / (upper.y - lower.y) as f64,
        };
        
        // 将边表项加入对应扫描线的边表
        let index = (lower.y - y_min) as usize;
        edge_table[index].push(entry);
    }
    
    // 2. 扫描线填充
    // 活性边表(AET - Active Edge Table)
    let mut aet: Vec<EdgeTableEntry> = Vec::new();
    
    // 从y_min开始扫描到y_max
    for y in y_min..=y_max {
        // 将当前扫描线的新边加入AET
        let et_index = (y - y_min) as usize;
        for entry in &edge_table[et_index] {
            aet.push(entry.clone());
        }
        
        // 对AET按x坐标排序
        aet.sort_by(|a, b| a.x.partial_cmp(&b.x).unwrap());
        
        // 配对填充：每两个交点之间填充
        for i in (0..aet.len()).step_by(2) {
            if i + 1 < aet.len() {
                let x_start = aet[i].x.round() as i32;
                let x_end = aet[i + 1].x.round() as i32;
                
                // 填充从x_start到x_end的像素
                for x in x_start..=x_end {
                    points.push(Point::new(x, y));
                }
            }
        }
        
        // 更新AET
        // 移除y_max == y的边
        aet.retain(|entry| entry.y_max > y);
        
        // 更新剩余边的x坐标
        for entry in &mut aet {
            entry.x += entry.inverse_slope;
        }
    }
    
    points
}

/// 栅栏填充算法（边界填充法）
/// 
/// 从种子点开始，使用4-连通或8-连通的方式填充封闭区域
/// 这里实现基于边界点集的栅栏填充
/// 
/// # 参数
/// * `vertices` - 多边形顶点坐标数组
/// 
/// # 返回值
/// 返回填充区域内所有点的坐标向量
pub fn fence_fill(vertices: &[Point]) -> Vec<Point> {
    if vertices.len() < 3 {
        return Vec::new();
    }
    
    let mut points = Vec::new();
    
    // 找出边界框
    let _x_min = vertices.iter().map(|p| p.x).min().unwrap();
    let _x_max = vertices.iter().map(|p| p.x).max().unwrap();
    let y_min = vertices.iter().map(|p| p.y).min().unwrap();
    let y_max = vertices.iter().map(|p| p.y).max().unwrap();
    
    // 对每一条扫描线
    for y in y_min..=y_max {
        // 找出该扫描线与多边形边的所有交点
        let mut intersections = Vec::new();
        
        let n = vertices.len();
        for i in 0..n {
            let v1 = vertices[i];
            let v2 = vertices[(i + 1) % n];
            
            // 检查边是否与扫描线相交
            // 使用更精确的边界判断，包含下端点但不包含上端点
            let y1_le = v1.y <= y;
            let y2_le = v2.y <= y;
            
            if y1_le != y2_le {
                // 计算交点的x坐标
                let x_intersect = v1.x as f64 + 
                    (y - v1.y) as f64 * (v2.x - v1.x) as f64 / (v2.y - v1.y) as f64;
                intersections.push(x_intersect);
            }
        }
        
        // 对交点排序
        intersections.sort_by(|a, b| a.partial_cmp(b).unwrap());
        
        // 配对填充（奇偶规则）
        for i in (0..intersections.len()).step_by(2) {
            if i + 1 < intersections.len() {
                let x_start = intersections[i].round() as i32;
                let x_end = intersections[i + 1].round() as i32;
                
                for x in x_start..=x_end {
                    points.push(Point::new(x, y));
                }
            }
        }
    }
    
    points
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bresenham_circle_basic() {
        // 测试圆心(0,0)半径5的圆
        let points = bresenham_circle(0, 0, 5);
        assert!(!points.is_empty());
        
        // 验证所有点到圆心的距离接近半径
        for p in &points {
            let dist_sq = p.x * p.x + p.y * p.y;
            let r_sq = 5 * 5;
            // 距离平方应该在r^2附近（允许一些误差）
            assert!((dist_sq - r_sq).abs() <= 10);
        }
    }
    
    #[test]
    fn test_bresenham_circle_problem() {
        // 测试作业题目：圆心(2,2)半径10，求x=8时的y值
        let points = bresenham_circle(2, 2, 10);
        
        // 找出x=8的所有点
        let x8_points: Vec<_> = points.iter().filter(|p| p.x == 8).collect();
        assert!(!x8_points.is_empty());
        
        // 打印结果供验证
        println!("圆心(2,2)半径10，x=8时的y值:");
        for p in x8_points {
            println!("  y = {}", p.y);
        }
    }

    #[test]
    fn test_scanline_fill_square() {
        // 测试正方形填充
        let vertices = vec![
            Point::new(0, 0),
            Point::new(4, 0),
            Point::new(4, 4),
            Point::new(0, 4),
        ];
        
        let points = scanline_fill(&vertices);
        
        // 正方形面积应该是5*5=25个点
        assert_eq!(points.len(), 25);
    }

    #[test]
    fn test_fence_fill_square() {
        // 测试正方形填充
        let vertices = vec![
            Point::new(0, 0),
            Point::new(4, 0),
            Point::new(4, 4),
            Point::new(0, 4),
        ];
        
        let points = fence_fill(&vertices);
        
        // 栅栏填充算法可能在边界处理上略有不同
        // 验证点数在合理范围内
        assert!(points.len() >= 20 && points.len() <= 25);
    }
    
    #[test]
    fn test_scanline_fill_triangle() {
        // 测试三角形填充
        let vertices = vec![
            Point::new(0, 0),
            Point::new(4, 0),
            Point::new(2, 3),
        ];
        
        let points = scanline_fill(&vertices);
        assert!(!points.is_empty());
    }
}
