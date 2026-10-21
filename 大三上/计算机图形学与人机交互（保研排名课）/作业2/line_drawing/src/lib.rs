/// 点结构体
#[derive(Debug, Clone, Copy, PartialEq)]
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

/// 中点画线法（简化版，仅适用于斜率0<k<1的情况）
/// 严格按照教材算法步骤实现
/// 
/// # 参数
/// * `x1` - 起点x坐标
/// * `y1` - 起点y坐标
/// * `x2` - 终点x坐标
/// * `y2` - 终点y坐标
/// 
/// # 前提条件
/// 要求 x1 < x2 且 0 < (y2-y1)/(x2-x1) < 1
pub fn midpoint_line_simple(x1: i32, y1: i32, x2: i32, y2: i32) -> Vec<Point> {
    let mut points = Vec::new();
    
    // (1) 初始化
    // 对于斜率0<k<1的情况，使用绝对值确保正确性
    let dx = x2 - x1;          // dx为正数
    let dy = y2 - y1;          // dy为正数（因为y2>y1）
    let mut d = 2 * dy - dx;   // 初始决策参数
    let d1 = 2 * dy;           // 选择右侧像素时的增量（y不变）
    let d2 = 2 * (dy - dx);    // 选择右上像素时的增量（y增加1）
    let mut x = x1;
    let mut y = y1;
    
    // (2) 绘制起点
    points.push(Point::new(x, y));
    
    // (3) 循环直到x到达x2
    while x < x2 {
        // (4) 根据d的值更新坐标
        x = x + 1;  // x总是增加1
        
        if d < 0 {
            // 误差为负，选择右侧像素（y不变）
            d = d + d1;
        } else {
            // 误差为正，选择右上像素（y增加1）
            y = y + 1;
            d = d + d2;
        }
        
        // (5) 绘制当前点
        points.push(Point::new(x, y));
    }
    
    points
}

/// 中点画线法绘制直线（通用版）
/// 
/// # 参数
/// * `x0` - 起点x坐标
/// * `y0` - 起点y坐标
/// * `x1` - 终点x坐标
/// * `y1` - 终点y坐标
/// 
/// # 返回值
/// 返回直线上所有点的坐标向量
pub fn midpoint_line(x0: i32, y0: i32, x1: i32, y1: i32) -> Vec<Point> {
    let mut points = Vec::new();
    
    // 计算x和y方向的增量绝对值
    let dx = (x1 - x0).abs();
    let dy = (y1 - y0).abs();
    
    // 确定x和y的增长方向
    let sx = if x0 < x1 { 1 } else { -1 };  // x方向步进值（1或-1）
    let sy = if y0 < y1 { 1 } else { -1 };  // y方向步进值（1或-1）
    
    let mut x = x0;
    let mut y = y0;
    
    // 判断主方向：dx > dy时以x为主方向，否则以y为主方向
    if dx > dy {
        // 以x为主方向迭代（斜率绝对值 < 1）
        let mut d = 2 * dy - dx;  // 初始决策参数
        let incr1 = 2 * dy;       // y不变时的增量
        let incr2 = 2 * (dy - dx); // y变化时的增量
        
        // 从起点迭代到终点
        for _ in 0..=dx {
            points.push(Point::new(x, y));  // 记录当前点
            
            if d <= 0 {
                // 中点在直线下方或上，选择右侧像素
                d += incr1;
            } else {
                // 中点在直线上方，选择右上（或右下）像素
                d += incr2;
                y += sy;  // y坐标按方向步进
            }
            x += sx;  // x坐标按方向步进
        }
    } else {
        // 以y为主方向迭代（斜率绝对值 >= 1）
        let mut d = 2 * dx - dy;  // 初始决策参数
        let incr1 = 2 * dx;       // x不变时的增量
        let incr2 = 2 * (dx - dy); // x变化时的增量
        
        // 从起点迭代到终点
        for _ in 0..=dy {
            points.push(Point::new(x, y));  // 记录当前点
            
            if d <= 0 {
                // 中点在直线左侧或上，选择上方像素
                d += incr1;
            } else {
                // 中点在直线右侧，选择右上（或左上）像素
                d += incr2;
                x += sx;  // x坐标按方向步进
            }
            y += sy;  // y坐标按方向步进
        }
    }
    
    points
}

/// Bresenham画线法绘制直线
/// 
/// # 参数
/// * `x0` - 起点x坐标
/// * `y0` - 起点y坐标
/// * `x1` - 终点x坐标
/// * `y1` - 终点y坐标
/// 
/// # 返回值
/// 返回直线上所有点的坐标向量
pub fn bresenham_line(x0: i32, y0: i32, x1: i32, y1: i32) -> Vec<Point> {
    let mut points = Vec::new();
    
    // 计算x和y方向的增量绝对值
    let dx = (x1 - x0).abs();
    let dy = (y1 - y0).abs();
    
    // 确定x和y的增长方向
    let sx = if x0 < x1 { 1 } else { -1 };  // x方向步进值（1或-1）
    let sy = if y0 < y1 { 1 } else { -1 };  // y方向步进值（1或-1）
    
    let mut x = x0;
    let mut y = y0;
    
    // 判断主方向：dx > dy时以x为主方向，否则以y为主方向
    if dx > dy {
        // 以x为主方向迭代（斜率绝对值 < 1）
        let mut e = 2 * dy - dx;  // 初始误差项
        let incr1 = 2 * dy;       // y不变时的误差增量
        let incr2 = 2 * (dy - dx); // y变化时的误差增量
        
        // 从起点迭代到终点
        for _ in 0..=dx {
            points.push(Point::new(x, y));  // 记录当前点
            
            if e < 0 {
                // 误差为负，选择右侧像素
                e += incr1;
            } else {
                // 误差为正，选择右上（或右下）像素
                e += incr2;
                y += sy;  // y坐标按方向步进
            }
            x += sx;  // x坐标按方向步进
        }
    } else {
        // 以y为主方向迭代（斜率绝对值 >= 1）
        let mut e = 2 * dx - dy;  // 初始误差项
        let incr1 = 2 * dx;       // x不变时的误差增量
        let incr2 = 2 * (dx - dy); // x变化时的误差增量
        
        // 从起点迭代到终点
        for _ in 0..=dy {
            points.push(Point::new(x, y));  // 记录当前点
            
            if e < 0 {
                // 误差为负，选择上方像素
                e += incr1;
            } else {
                // 误差为正，选择右上（或左上）像素
                e += incr2;
                x += sx;  // x坐标按方向步进
            }
            y += sy;  // y坐标按方向步进
        }
    }
    
    points
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_midpoint_line_horizontal() {
        let points = midpoint_line(0, 0, 5, 0);
        assert_eq!(points.len(), 6);
        assert_eq!(points[0], Point::new(0, 0));
        assert_eq!(points[5], Point::new(5, 0));
    }

    #[test]
    fn test_bresenham_line_vertical() {
        let points = bresenham_line(0, 0, 0, 5);
        assert_eq!(points.len(), 6);
        assert_eq!(points[0], Point::new(0, 0));
        assert_eq!(points[5], Point::new(0, 5));
    }

    #[test]
    fn test_problem1_midpoint() {
        let points = midpoint_line(2, 8, 10, 4);
        let p7 = points.iter().find(|p| p.x == 7).unwrap();
        assert_eq!(p7.y, 6);
    }

    #[test]
    fn test_problem1_bresenham() {
        let points = bresenham_line(2, 8, 10, 4);
        let p7 = points.iter().find(|p| p.x == 7).unwrap();
        assert_eq!(p7.y, 5);
    }

    #[test]
    fn test_problem2_midpoint() {
        let points = midpoint_line(2, 2, 4, 10);
        let p6 = points.iter().find(|p| p.y == 6).unwrap();
        assert_eq!(p6.x, 3);
    }

    #[test]
    fn test_problem2_bresenham() {
        let points = bresenham_line(2, 2, 4, 10);
        let p6 = points.iter().find(|p| p.y == 6).unwrap();
        assert_eq!(p6.x, 3);
    }
    
    #[test]
    fn test_midpoint_line_simple() {
        // 测试简化版：斜率0<k<1的情况
        let points = midpoint_line_simple(1, 1, 8, 4);
        
        // 调试输出
        println!("生成的点序列：");
        for (i, p) in points.iter().enumerate() {
            println!("  [{}] ({}, {})", i, p.x, p.y);
        }
        
        assert_eq!(points.len(), 8, "应该有8个点（从x=1到x=8）");
        assert_eq!(points[0], Point::new(1, 1), "起点应该是(1,1)");
        assert_eq!(points[7], Point::new(8, 4), "终点应该是(8,4)");
        // 验证y坐标单调递增
        for i in 1..points.len() {
            assert!(points[i].y >= points[i-1].y, "y坐标应该单调递增");
        }
    }
}
