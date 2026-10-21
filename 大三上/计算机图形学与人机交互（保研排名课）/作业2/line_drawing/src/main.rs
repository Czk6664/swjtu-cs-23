use line_drawing::{midpoint_line, bresenham_line, midpoint_line_simple};

fn main() {
    println!("╔═══════════════════════════════════════════════════════════════╗");
    println!("║          直线绘制算法 - Rust实现                              ║");
    println!("║    中点画线法 (Midpoint Line Algorithm)                       ║");
    println!("║    Bresenham画线法 (Bresenham Line Algorithm)                 ║");
    println!("╚═══════════════════════════════════════════════════════════════╝");
    
    // 测试简化版中点画线法（仅适用于0<k<1）
    println!("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("【测试1】简化版中点画线法（仅适用于斜率 0 < k < 1）");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("测试直线：从(1,1)到(8,4)，斜率 k = 3/7 ≈ 0.43");
    let points_simple = midpoint_line_simple(1, 1, 8, 4);
    print!("绘制点序列：");
    for (i, p) in points_simple.iter().enumerate() {
        if i > 0 { print!(" → "); }
        print!("({}, {})", p.x, p.y);
    }
    println!("\n");
    
    // 问题1：起点(2,8)，终点(10,4)，求x=7时的y值
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("【问题1】起点(2,8)，终点(10,4)，求 x=7 时的 y 值");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Δx = 8, Δy = -4, 斜率 k = -0.5\n");
    
    println!("【中点画线法】");
    let points1 = midpoint_line(2, 8, 10, 4);
    print!("绘制点序列：");
    for (i, p) in points1.iter().enumerate() {
        if i > 0 { print!(" → "); }
        print!("({}, {})", p.x, p.y);
        if p.x == 7 {
            print!(" ★");
        }
    }
    println!();
    if let Some(p) = points1.iter().find(|p| p.x == 7) {
        println!("✓ 答案：当 x = 7 时，y = {}", p.y);
    }
    
    println!("\n【Bresenham画线法】");
    let points2 = bresenham_line(2, 8, 10, 4);
    print!("绘制点序列：");
    for (i, p) in points2.iter().enumerate() {
        if i > 0 { print!(" → "); }
        print!("({}, {})", p.x, p.y);
        if p.x == 7 {
            print!(" ★");
        }
    }
    println!();
    if let Some(p) = points2.iter().find(|p| p.x == 7) {
        println!("✓ 答案：当 x = 7 时，y = {}", p.y);
    }
    
    // 问题2：起点(2,2)，终点(4,10)，求y=6时的x值
    println!("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("【问题2】起点(2,2)，终点(4,10)，求 y=6 时的 x 值");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Δx = 2, Δy = 8, 斜率 k = 4\n");
    
    println!("【中点画线法】");
    let points3 = midpoint_line(2, 2, 4, 10);
    print!("绘制点序列：");
    for (i, p) in points3.iter().enumerate() {
        if i > 0 { print!(" → "); }
        print!("({}, {})", p.x, p.y);
        if p.y == 6 {
            print!(" ★");
        }
    }
    println!();
    if let Some(p) = points3.iter().find(|p| p.y == 6) {
        println!("✓ 答案：当 y = 6 时，x = {}", p.x);
    }
    
    println!("\n【Bresenham画线法】");
    let points4 = bresenham_line(2, 2, 4, 10);
    print!("绘制点序列：");
    for (i, p) in points4.iter().enumerate() {
        if i > 0 { print!(" → "); }
        print!("({}, {})", p.x, p.y);
        if p.y == 6 {
            print!(" ★");
        }
    }
    println!();
    if let Some(p) = points4.iter().find(|p| p.y == 6) {
        println!("✓ 答案：当 y = 6 时，x = {}", p.x);
    }
    
    // 算法对比
    println!("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("【算法对比总结】");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("问题1 (2,8)→(10,4)，x=7时：");
    println!("  • 中点画线法：y = 6");
    println!("  • Bresenham法：y = 5");
    println!("\n问题2 (2,2)→(4,10)，y=6时：");
    println!("  • 中点画线法：x = 3");
    println!("  • Bresenham法：x = 3");
    println!("\n说明：两种算法在某些情况下会产生略微不同的结果，");
    println!("      这是由于判断条件的细微差异造成的（d≤0 vs e<0）。");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
}
