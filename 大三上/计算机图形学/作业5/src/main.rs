// 计算机图形学 作业5
// 2023112621 程泽凯

mod vector;
mod midpoint_clip;
mod sutherland_hodgman;
mod weiler_atherton;

fn main() {
    println!("╔════════════════════════════════════════╗");
    println!("║     计算机图形学 作业5 - 程泽凯        ║");
    println!("╚════════════════════════════════════════╝\n");

    println!("############################################");
    println!("#  题目2: 三维向量模长与夹角               #");
    println!("############################################");
    vector::demo();
    println!("\n");

    println!("############################################");
    println!("#  题目3: 中点分割线段裁剪                 #");
    println!("############################################");
    midpoint_clip::demo();
    println!("\n");

    println!("############################################");
    println!("#  题目4: Sutherland-Hodgman多边形裁剪     #");
    println!("############################################");
    sutherland_hodgman::demo();
    println!("\n");

    println!("############################################");
    println!("#  题目5: Weiler-Atherton多边形裁剪        #");
    println!("############################################");
    weiler_atherton::demo();
    
    println!("\n[程序结束]");
}
