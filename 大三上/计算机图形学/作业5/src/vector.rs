// 第2题：三维矢量长度与夹角计算

/// 三维向量结构体
#[derive(Debug, Clone, Copy)]
pub struct Vec3 {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Vec3 {
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Vec3 { x, y, z }
    }

    /// 计算向量长度
    pub fn length(&self) -> f64 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    /// 计算点积
    pub fn dot(&self, other: &Vec3) -> f64 {
        self.x * other.x + self.y * other.y + self.z * other.z
    }

    /// 计算两向量夹角（弧度）
    pub fn angle_with(&self, other: &Vec3) -> f64 {
        let len_product = self.length() * other.length();
        if len_product < 1e-10 {
            return 0.0;
        }
        let cos_theta = (self.dot(other) / len_product).clamp(-1.0, 1.0);
        cos_theta.acos()
    }

    /// 计算两向量夹角（角度）
    pub fn angle_degrees(&self, other: &Vec3) -> f64 {
        self.angle_with(other).to_degrees()
    }
}

/// 演示函数
pub fn demo() {
    let u = Vec3::new(3.0, -1.0, 4.0);
    let v = Vec3::new(2.0, 5.0, -2.0);

    println!("给定两个三维向量:");
    println!("  u = ({}, {}, {})", u.x, u.y, u.z);
    println!("  v = ({}, {}, {})", v.x, v.y, v.z);
    println!();

    // 向量u长度
    let len_u = u.length();
    println!(">>> 计算向量u的模长");
    println!("    |u| = √({}² + ({})² + {}²)", u.x, u.y, u.z);
    println!("        = √({} + {} + {})", u.x*u.x, u.y*u.y, u.z*u.z);
    println!("        = √{} ≈ {:.4}", u.x*u.x + u.y*u.y + u.z*u.z, len_u);
    println!();

    // 向量v长度
    let len_v = v.length();
    println!(">>> 计算向量v的模长");
    println!("    |v| = √({}² + {}² + ({})²)", v.x, v.y, v.z);
    println!("        = √({} + {} + {})", v.x*v.x, v.y*v.y, v.z*v.z);
    println!("        = √{} ≈ {:.4}", v.x*v.x + v.y*v.y + v.z*v.z, len_v);
    println!();

    // 点积
    let dot_val = u.dot(&v);
    println!(">>> 计算点积 u·v");
    println!("    u·v = ({})×({}) + ({})×({}) + ({})×({})", u.x, v.x, u.y, v.y, u.z, v.z);
    println!("        = {} + ({}) + ({})", u.x*v.x, u.y*v.y, u.z*v.z);
    println!("        = {}", dot_val);
    println!();

    // 夹角
    let cos_theta = dot_val / (len_u * len_v);
    let theta_rad = u.angle_with(&v);
    let theta_deg = u.angle_degrees(&v);

    println!(">>> 计算夹角θ");
    println!("    cosθ = (u·v)/(|u||v|) = {}/({:.4}×{:.4})", dot_val, len_u, len_v);
    println!("         = {}/{:.4} = {:.6}", dot_val, len_u * len_v, cos_theta);
    println!("    θ = arccos({:.6})", cos_theta);
    println!("      = {:.4} rad = {:.2}°", theta_rad, theta_deg);
}
