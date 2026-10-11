use circle_polygon::{Point, bresenham_circle, scanline_fill, fence_fill};

fn main() {
    println!("=======================================");
    println!("    计算机图形学作业3 - 圆与多边形填充");
    println!("=======================================\n");
    
    // 第一题：Bresenham圆绘制
    println!("【第一题】Bresenham圆绘制算法");
    println!("---------------------------------------");
    
    // 题目要求：圆心(2,2)，半径10，求x=8时的y值
    println!("\n问题：圆心(2,2)，半径10，求x=8时的y值");
    let circle_points = bresenham_circle(2, 2, 10);
    
    // 找出x=8的所有点
    let x8_points: Vec<_> = circle_points.iter()
        .filter(|p| p.x == 8)
        .collect();
    
    println!("\n圆上所有点的数量: {}", circle_points.len());
    println!("\n当x=8时，y的值为:");
    for p in &x8_points {
        println!("  Point({}, {})", p.x, p.y);
    }
    
    // 显示圆的所有点坐标
    println!("\n圆的所有点坐标（共{}个点）:", circle_points.len());
    println!("\n按象限分类显示：");
    
    // 第一象限
    println!("\n【第一象限】(x >= 2, y >= 2):");
    let first_quadrant: Vec<_> = circle_points.iter()
        .filter(|p| p.x >= 2 && p.y >= 2)
        .collect();
    for (i, p) in first_quadrant.iter().enumerate() {
        print!("({:2}, {:2})  ", p.x, p.y);
        if (i + 1) % 6 == 0 {
            println!();
        }
    }
    println!("\n共 {} 个点", first_quadrant.len());
    
    // 第二象限
    println!("\n【第二象限】(x < 2, y >= 2):");
    let second_quadrant: Vec<_> = circle_points.iter()
        .filter(|p| p.x < 2 && p.y >= 2)
        .collect();
    for (i, p) in second_quadrant.iter().enumerate() {
        print!("({:2}, {:2})  ", p.x, p.y);
        if (i + 1) % 6 == 0 {
            println!();
        }
    }
    println!("\n共 {} 个点", second_quadrant.len());
    
    // 第三象限
    println!("\n【第三象限】(x < 2, y < 2):");
    let third_quadrant: Vec<_> = circle_points.iter()
        .filter(|p| p.x < 2 && p.y < 2)
        .collect();
    for (i, p) in third_quadrant.iter().enumerate() {
        print!("({:2}, {:2})  ", p.x, p.y);
        if (i + 1) % 6 == 0 {
            println!();
        }
    }
    println!("\n共 {} 个点", third_quadrant.len());
    
    // 第四象限
    println!("\n【第四象限】(x >= 2, y < 2):");
    let fourth_quadrant: Vec<_> = circle_points.iter()
        .filter(|p| p.x >= 2 && p.y < 2)
        .collect();
    for (i, p) in fourth_quadrant.iter().enumerate() {
        print!("({:2}, {:2})  ", p.x, p.y);
        if (i + 1) % 6 == 0 {
            println!();
        }
    }
    println!("\n共 {} 个点", fourth_quadrant.len());
    
    // 所有点（按坐标排序）
    println!("\n【所有点按坐标排序】:");
    for (i, p) in circle_points.iter().enumerate() {
        print!("({:2}, {:2})  ", p.x, p.y);
        if (i + 1) % 6 == 0 {
            println!();
        }
    }
    println!();
    
    // 第二题：多边形填充
    println!("\n\n【第二题】多边形填充算法");
    println!("---------------------------------------");
    
    // 测试用多边形1：简单正方形
    println!("\n测试1: 正方形多边形 (0,0) (10,0) (10,10) (0,10)");
    let square = vec![
        Point::new(0, 0),
        Point::new(10, 0),
        Point::new(10, 10),
        Point::new(0, 10),
    ];
    
    println!("\n(1) 扫描线填充算法:");
    let scanline_points = scanline_fill(&square);
    println!("  填充点数: {}", scanline_points.len());
    println!("  理论点数: {}", 11 * 11); // (10-0+1) * (10-0+1)
    
    println!("\n(2) 栅栏填充算法:");
    let fence_points = fence_fill(&square);
    println!("  填充点数: {}", fence_points.len());
    
    // 测试用多边形2：三角形
    println!("\n\n测试2: 三角形多边形 (0,0) (10,0) (5,8)");
    let triangle = vec![
        Point::new(0, 0),
        Point::new(10, 0),
        Point::new(5, 8),
    ];
    
    println!("\n(1) 扫描线填充算法:");
    let scanline_tri = scanline_fill(&triangle);
    println!("  填充点数: {}", scanline_tri.len());
    
    // 显示部分填充点
    println!("  部分填充点坐标（前20个）:");
    for (i, p) in scanline_tri.iter().take(20).enumerate() {
        print!("({:2},{:2})  ", p.x, p.y);
        if (i + 1) % 5 == 0 {
            println!();
        }
    }
    println!();
    
    println!("\n(2) 栅栏填充算法:");
    let fence_tri = fence_fill(&triangle);
    println!("  填充点数: {}", fence_tri.len());
    
    // 测试用多边形3：复杂多边形（五边形）
    println!("\n\n测试3: 五边形多边形");
    let pentagon = vec![
        Point::new(5, 0),
        Point::new(10, 4),
        Point::new(8, 10),
        Point::new(2, 10),
        Point::new(0, 4),
    ];
    
    println!("\n顶点坐标:");
    for (i, p) in pentagon.iter().enumerate() {
        println!("  顶点{}: ({}, {})", i + 1, p.x, p.y);
    }
    
    println!("\n(1) 扫描线填充算法:");
    let scanline_pent = scanline_fill(&pentagon);
    println!("  填充点数: {}", scanline_pent.len());
    
    println!("\n(2) 栅栏填充算法:");
    let fence_pent = fence_fill(&pentagon);
    println!("  填充点数: {}", fence_pent.len());
    
    // 性能比较
    println!("\n\n【算法性能比较】");
    println!("---------------------------------------");
    println!("多边形类型     | 扫描线填充 | 栅栏填充");
    println!("---------------|-----------|----------");
    println!("正方形(11x11)  | {:9} | {:8}", scanline_points.len(), fence_points.len());
    println!("三角形         | {:9} | {:8}", scanline_tri.len(), fence_tri.len());
    println!("五边形         | {:9} | {:8}", scanline_pent.len(), fence_pent.len());
    
    println!("\n=======================================");
    println!("           程序执行完毕");
    println!("=======================================\n");
}
