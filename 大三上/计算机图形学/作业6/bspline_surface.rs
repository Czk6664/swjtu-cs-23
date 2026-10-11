//! 三阶B样条曲面计算程序
//! 
//! 计算机图形学 作业6 第2题
//! 
//! 功能：
//! - 根据给定控制点计算B样条曲面
//! - 支持自定义u、v方向的曲面精度
//! - 生成三角形网格的顶点和索引数组

use std::fmt;

// ============================================================================
// 数据结构定义
// ============================================================================

/// 三维点/向量结构
#[derive(Clone, Copy)]
pub struct Point3 {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Point3 {
    /// 创建新的三维点
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z }
    }

    /// 创建零点
    pub fn zero() -> Self {
        Self { x: 0.0, y: 0.0, z: 0.0 }
    }
}

impl fmt::Debug for Point3 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({:.4}, {:.4}, {:.4})", self.x, self.y, self.z)
    }
}

impl fmt::Display for Point3 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({:.4}, {:.4}, {:.4})", self.x, self.y, self.z)
    }
}

/// 实现点的加法运算
impl std::ops::Add for Point3 {
    type Output = Self;
    fn add(self, other: Self) -> Self {
        Self {
            x: self.x + other.x,
            y: self.y + other.y,
            z: self.z + other.z,
        }
    }
}

/// 实现点与标量的乘法运算
impl std::ops::Mul<f64> for Point3 {
    type Output = Self;
    fn mul(self, scalar: f64) -> Self {
        Self {
            x: self.x * scalar,
            y: self.y * scalar,
            z: self.z * scalar,
        }
    }
}

// ============================================================================
// B样条曲面结构
// ============================================================================

/// 三阶B样条曲面
/// 
/// 使用Cox-de Boor递推公式计算B样条基函数，
/// 支持任意m×n控制点网格的曲面生成。
pub struct BSplineSurface {
    /// m × n 控制点网格
    control_points: Vec<Vec<Point3>>,
    /// u方向节点向量
    knots_u: Vec<f64>,
    /// v方向节点向量
    knots_v: Vec<f64>,
    /// 曲线次数（三阶B样条为3）
    degree: usize,
    /// u方向控制点数量
    m: usize,
    /// v方向控制点数量
    n: usize,
}

impl BSplineSurface {
    /// 创建三阶B样条曲面
    /// 
    /// # 参数
    /// - `control_points`: m × n 控制点网格，至少需要4×4个控制点
    /// 
    /// # 返回
    /// - `Result<Self, String>`: 成功返回曲面对象，失败返回错误信息
    /// 
    /// # 示例
    /// ```
    /// let points = vec![
    ///     vec![Point3::new(0.0, 0.0, 0.0), ...],
    ///     ...
    /// ];
    /// let surface = BSplineSurface::new(points)?;
    /// ```
    pub fn new(control_points: Vec<Vec<Point3>>) -> Result<Self, String> {
        let m = control_points.len();
        if m < 4 {
            return Err(format!(
                "三阶B样条曲面至少需要4行控制点，当前只有{}行", m
            ));
        }

        let n = control_points[0].len();
        if n < 4 {
            return Err(format!(
                "三阶B样条曲面至少需要4列控制点，当前只有{}列", n
            ));
        }

        // 验证控制点网格是否规则
        for (i, row) in control_points.iter().enumerate() {
            if row.len() != n {
                return Err(format!(
                    "控制点网格不规则：第{}行有{}个点，期望{}个", 
                    i, row.len(), n
                ));
            }
        }

        let degree = 3; // 三阶B样条，次数为3

        // 生成均匀开放节点向量
        let knots_u = Self::generate_uniform_knots(m, degree);
        let knots_v = Self::generate_uniform_knots(n, degree);

        Ok(Self {
            control_points,
            knots_u,
            knots_v,
            degree,
            m,
            n,
        })
    }

    /// 生成均匀开放节点向量
    /// 
    /// 对于n个控制点和p次B样条，节点向量包含n+p+1个节点。
    /// 均匀开放节点向量的特点：
    /// - 前p+1个节点为0
    /// - 后p+1个节点为1
    /// - 中间节点均匀分布
    /// 
    /// # 参数
    /// - `n`: 控制点数量
    /// - `degree`: 曲线次数
    /// 
    /// # 返回
    /// - 节点向量
    fn generate_uniform_knots(n: usize, degree: usize) -> Vec<f64> {
        let num_knots = n + degree + 1;
        let mut knots = Vec::with_capacity(num_knots);
        
        for i in 0..num_knots {
            if i <= degree {
                // 前degree+1个节点为0，确保曲线通过第一个控制点
                knots.push(0.0);
            } else if i >= num_knots - degree - 1 {
                // 后degree+1个节点为1，确保曲线通过最后一个控制点
                knots.push(1.0);
            } else {
                // 中间节点均匀分布
                let val = (i - degree) as f64 / (num_knots - 2 * degree - 1) as f64;
                knots.push(val);
            }
        }
        knots
    }

    /// Cox-de Boor递推公式计算B样条基函数
    /// 
    /// 递推公式：
    /// N_{i,0}(t) = 1 if t_i <= t < t_{i+1}, else 0
    /// N_{i,p}(t) = (t-t_i)/(t_{i+p}-t_i) * N_{i,p-1}(t) 
    ///            + (t_{i+p+1}-t)/(t_{i+p+1}-t_{i+1}) * N_{i+1,p-1}(t)
    /// 
    /// # 参数
    /// - `i`: 基函数索引
    /// - `p`: 当前递推的次数
    /// - `t`: 参数值，范围[0,1]
    /// - `knots`: 节点向量
    /// 
    /// # 返回
    /// - 基函数值 N_{i,p}(t)
    fn basis_function(&self, i: usize, p: usize, t: f64, knots: &[f64]) -> f64 {
        // 零次基函数（递推基础）
        if p == 0 {
            // 标准情况：t在[t_i, t_{i+1})区间内
            if knots[i] <= t && t < knots[i + 1] {
                return 1.0;
            }
            // 边界情况：处理t=1.0时的特殊情况
            // 当t=1.0且t_{i+1}=1.0时，应返回1
            if (t - 1.0).abs() < 1e-10 && (knots[i + 1] - 1.0).abs() < 1e-10 {
                return 1.0;
            }
            return 0.0;
        }

        // 递推计算高次基函数
        let mut result = 0.0;

        // 第一项：(t-t_i)/(t_{i+p}-t_i) * N_{i,p-1}(t)
        let denom1 = knots[i + p] - knots[i];
        if denom1.abs() > 1e-10 {
            // 分母不为零时计算
            result += (t - knots[i]) / denom1 * self.basis_function(i, p - 1, t, knots);
        }
        // 分母为零时，约定该项为0（0/0 = 0）

        // 第二项：(t_{i+p+1}-t)/(t_{i+p+1}-t_{i+1}) * N_{i+1,p-1}(t)
        let denom2 = knots[i + p + 1] - knots[i + 1];
        if denom2.abs() > 1e-10 {
            result += (knots[i + p + 1] - t) / denom2 
                    * self.basis_function(i + 1, p - 1, t, knots);
        }

        result
    }

    /// 计算曲面上一点 S(u,v)
    /// 
    /// B样条曲面方程：
    /// S(u,v) = Σ_i Σ_j N_{i,p}(u) * N_{j,q}(v) * P_{i,j}
    /// 
    /// # 参数
    /// - `u`: u方向参数，范围[0,1]
    /// - `v`: v方向参数，范围[0,1]
    /// 
    /// # 返回
    /// - 曲面上的点坐标
    pub fn evaluate(&self, u: f64, v: f64) -> Point3 {
        let mut point = Point3::zero();

        // 双重求和计算曲面点
        for i in 0..self.m {
            // 计算u方向基函数值
            let basis_u = self.basis_function(i, self.degree, u, &self.knots_u);
            
            // 如果基函数值为0，跳过内层循环（优化）
            if basis_u.abs() < 1e-10 {
                continue;
            }

            for j in 0..self.n {
                // 计算v方向基函数值
                let basis_v = self.basis_function(j, self.degree, v, &self.knots_v);
                
                // 计算权重
                let weight = basis_u * basis_v;
                
                // 累加贡献
                if weight.abs() > 1e-10 {
                    point = point + self.control_points[i][j] * weight;
                }
            }
        }

        point
    }

    /// 生成曲面网格（顶点和三角形索引）
    /// 
    /// 将参数域[0,1]×[0,1]离散化，生成三角形网格。
    /// 每个网格单元划分为两个三角形。
    /// 
    /// # 参数
    /// - `u_resolution`: u方向细分段数
    /// - `v_resolution`: v方向细分段数
    /// 
    /// # 返回
    /// - `(Vec<Point3>, Vec<[usize; 3]>)`: (顶点数组, 三角形索引数组)
    /// 
    /// # 说明
    /// - 顶点数量: (u_resolution + 1) × (v_resolution + 1)
    /// - 三角形数量: 2 × u_resolution × v_resolution
    pub fn generate_mesh(&self, u_resolution: usize, v_resolution: usize) 
        -> (Vec<Point3>, Vec<[usize; 3]>) 
    {
        let num_vertices = (u_resolution + 1) * (v_resolution + 1);
        let num_triangles = 2 * u_resolution * v_resolution;
        
        let mut vertices = Vec::with_capacity(num_vertices);
        let mut indices = Vec::with_capacity(num_triangles);

        // ====== 第一步：生成曲面上的顶点 ======
        // 遍历参数域，计算每个采样点的坐标
        for i in 0..=u_resolution {
            let u = i as f64 / u_resolution as f64;
            for j in 0..=v_resolution {
                let v = j as f64 / v_resolution as f64;
                vertices.push(self.evaluate(u, v));
            }
        }

        // ====== 第二步：生成三角形索引 ======
        // 每个网格单元划分为两个三角形
        //
        //  (i,j+1) -------- (i+1,j+1)
        //     |  \    T1    |
        //     |    \        |
        //     |  T2  \      |
        //     |        \    |
        //  (i,j) -------- (i+1,j)
        //
        let cols = v_resolution + 1;
        for i in 0..u_resolution {
            for j in 0..v_resolution {
                // 计算当前网格单元四个角的顶点索引
                let bottom_left = i * cols + j;
                let bottom_right = i * cols + (j + 1);
                let top_left = (i + 1) * cols + j;
                let top_right = (i + 1) * cols + (j + 1);
                
                // 三角形1: 左下 -> 右下 -> 右上（逆时针）
                indices.push([bottom_left, bottom_right, top_right]);
                
                // 三角形2: 左下 -> 右上 -> 左上（逆时针）
                indices.push([bottom_left, top_right, top_left]);
            }
        }

        (vertices, indices)
    }

    /// 获取控制点网格尺寸
    pub fn get_control_point_size(&self) -> (usize, usize) {
        (self.m, self.n)
    }

    /// 获取曲线次数
    pub fn get_degree(&self) -> usize {
        self.degree
    }

    /// 打印节点向量信息（调试用）
    pub fn print_knot_vectors(&self) {
        println!("u方向节点向量 ({} 个节点):", self.knots_u.len());
        print!("  [");
        for (i, k) in self.knots_u.iter().enumerate() {
            if i > 0 { print!(", "); }
            print!("{:.3}", k);
        }
        println!("]");

        println!("v方向节点向量 ({} 个节点):", self.knots_v.len());
        print!("  [");
        for (i, k) in self.knots_v.iter().enumerate() {
            if i > 0 { print!(", "); }
            print!("{:.3}", k);
        }
        println!("]");
    }
}

// ============================================================================
// 主函数和测试
// ============================================================================

fn main() {
    println!("╔══════════════════════════════════════════════════════════════╗");
    println!("║           三阶B样条曲面生成程序                              ║");
    println!("║           计算机图形学 作业6 第2题                           ║");
    println!("╚══════════════════════════════════════════════════════════════╝\n");

    // ====== 定义控制点网格 ======
    // 创建 4×4 控制点网格（三阶B样条至少需要4个控制点）
    // 这里创建一个类似"山丘"形状的曲面
    let control_points = vec![
        // 第0行 (u=0)
        vec![
            Point3::new(0.0, 0.0, 0.0),
            Point3::new(1.0, 0.0, 1.0),
            Point3::new(2.0, 0.0, 1.0),
            Point3::new(3.0, 0.0, 0.0),
        ],
        // 第1行
        vec![
            Point3::new(0.0, 1.0, 1.0),
            Point3::new(1.0, 1.0, 2.0),
            Point3::new(2.0, 1.0, 2.0),
            Point3::new(3.0, 1.0, 1.0),
        ],
        // 第2行
        vec![
            Point3::new(0.0, 2.0, 1.0),
            Point3::new(1.0, 2.0, 2.0),
            Point3::new(2.0, 2.0, 2.0),
            Point3::new(3.0, 2.0, 1.0),
        ],
        // 第3行 (u=1)
        vec![
            Point3::new(0.0, 3.0, 0.0),
            Point3::new(1.0, 3.0, 1.0),
            Point3::new(2.0, 3.0, 1.0),
            Point3::new(3.0, 3.0, 0.0),
        ],
    ];

    // ====== 创建B样条曲面 ======
    let surface = match BSplineSurface::new(control_points) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("错误: {}", e);
            return;
        }
    };

    // 打印曲面信息
    let (m, n) = surface.get_control_point_size();
    println!("【曲面参数】");
    println!("  控制点网格: {} × {}", m, n);
    println!("  曲线次数: {} (三阶B样条)", surface.get_degree());
    println!();

    // 打印节点向量
    println!("【节点向量】");
    surface.print_knot_vectors();
    println!();

    // ====== 设置曲面精度参数 ======
    let u_resolution = 10;  // u方向细分段数
    let v_resolution = 10;  // v方向细分段数

    println!("【曲面精度设置】");
    println!("  u方向细分: {} 段", u_resolution);
    println!("  v方向细分: {} 段", v_resolution);
    println!();

    // ====== 生成曲面网格 ======
    let (vertices, indices) = surface.generate_mesh(u_resolution, v_resolution);

    // ====== 输出结果统计 ======
    println!("【生成结果】");
    println!("  顶点数量: {}", vertices.len());
    println!("  三角形数量: {}", indices.len());
    println!();

    // ====== 输出顶点数组（部分） ======
    println!("【顶点数组】(前15个)");
    println!("  {:>4}  {:>30}", "索引", "坐标 (x, y, z)");
    println!("  {}", "-".repeat(40));
    for (i, v) in vertices.iter().take(15).enumerate() {
        println!("  V{:<3}  {}", i, v);
    }
    if vertices.len() > 15 {
        println!("  ... (共{}个顶点)", vertices.len());
    }
    println!();

    // ====== 输出三角形索引数组（部分） ======
    println!("【三角形索引数组】(前15个)");
    println!("  {:>4}  {:>20}", "索引", "顶点索引 [v0, v1, v2]");
    println!("  {}", "-".repeat(30));
    for (i, tri) in indices.iter().take(15).enumerate() {
        println!("  T{:<3}  [{:>3}, {:>3}, {:>3}]", i, tri[0], tri[1], tri[2]);
    }
    if indices.len() > 15 {
        println!("  ... (共{}个三角形)", indices.len());
    }
    println!();

    // ====== 验证：计算特定参数点 ======
    println!("【曲面采样验证】");
    let test_points = [
        (0.0, 0.0, "左下角"),
        (1.0, 0.0, "右下角"),
        (0.0, 1.0, "左上角"),
        (1.0, 1.0, "右上角"),
        (0.5, 0.5, "中心点"),
        (0.25, 0.75, "任意点"),
    ];

    for (u, v, desc) in test_points.iter() {
        let point = surface.evaluate(*u, *v);
        println!("  S({:.2}, {:.2}) = {} ({})", u, v, point, desc);
    }

    println!("\n程序执行完成！");
}

// ============================================================================
// 单元测试
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    /// 创建测试用的4×4控制点网格
    fn create_test_control_points() -> Vec<Vec<Point3>> {
        vec![
            vec![
                Point3::new(0.0, 0.0, 0.0),
                Point3::new(1.0, 0.0, 0.0),
                Point3::new(2.0, 0.0, 0.0),
                Point3::new(3.0, 0.0, 0.0),
            ],
            vec![
                Point3::new(0.0, 1.0, 0.0),
                Point3::new(1.0, 1.0, 1.0),
                Point3::new(2.0, 1.0, 1.0),
                Point3::new(3.0, 1.0, 0.0),
            ],
            vec![
                Point3::new(0.0, 2.0, 0.0),
                Point3::new(1.0, 2.0, 1.0),
                Point3::new(2.0, 2.0, 1.0),
                Point3::new(3.0, 2.0, 0.0),
            ],
            vec![
                Point3::new(0.0, 3.0, 0.0),
                Point3::new(1.0, 3.0, 0.0),
                Point3::new(2.0, 3.0, 0.0),
                Point3::new(3.0, 3.0, 0.0),
            ],
        ]
    }

    #[test]
    fn test_surface_creation() {
        let control_points = create_test_control_points();
        let surface = BSplineSurface::new(control_points);
        assert!(surface.is_ok());
        
        let surface = surface.unwrap();
        assert_eq!(surface.get_control_point_size(), (4, 4));
        assert_eq!(surface.get_degree(), 3);
    }

    #[test]
    fn test_insufficient_control_points() {
        // 测试控制点不足的情况
        let control_points = vec![
            vec![Point3::new(0.0, 0.0, 0.0), Point3::new(1.0, 0.0, 0.0)],
            vec![Point3::new(0.0, 1.0, 0.0), Point3::new(1.0, 1.0, 0.0)],
        ];
        let surface = BSplineSurface::new(control_points);
        assert!(surface.is_err());
    }

    #[test]
    fn test_mesh_generation() {
        let control_points = create_test_control_points();
        let surface = BSplineSurface::new(control_points).unwrap();
        
        let (vertices, indices) = surface.generate_mesh(5, 5);
        
        // 验证顶点数量: (5+1) × (5+1) = 36
        assert_eq!(vertices.len(), 36);
        
        // 验证三角形数量: 2 × 5 × 5 = 50
        assert_eq!(indices.len(), 50);
    }

    #[test]
    fn test_corner_points() {
        let control_points = create_test_control_points();
        let surface = BSplineSurface::new(control_points).unwrap();
        
        // 测试四个角点（应该接近控制点的角点）
        let p00 = surface.evaluate(0.0, 0.0);
        let p10 = surface.evaluate(1.0, 0.0);
        let p01 = surface.evaluate(0.0, 1.0);
        let p11 = surface.evaluate(1.0, 1.0);
        
        // 验证角点坐标（允许小误差）
        assert!((p00.x - 0.0).abs() < 0.01);
        assert!((p00.y - 0.0).abs() < 0.01);
        
        assert!((p10.x - 3.0).abs() < 0.01);
        assert!((p11.y - 3.0).abs() < 0.01);
    }

    #[test]
    fn test_triangle_indices_validity() {
        let control_points = create_test_control_points();
        let surface = BSplineSurface::new(control_points).unwrap();
        
        let (vertices, indices) = surface.generate_mesh(3, 3);
        
        // 验证所有三角形索引都在有效范围内
        for tri in &indices {
            assert!(tri[0] < vertices.len());
            assert!(tri[1] < vertices.len());
            assert!(tri[2] < vertices.len());
        }
    }
}
