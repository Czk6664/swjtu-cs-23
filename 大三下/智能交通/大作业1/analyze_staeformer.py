"""
STAEformer Deep Analysis Script
"""

import torch
import torch.nn as nn
import numpy as np

class AttentionLayer(nn.Module):
    def __init__(self, model_dim, num_heads=8, mask=False):
        super().__init__()
        self.model_dim = model_dim
        self.num_heads = num_heads
        self.mask = mask
        self.head_dim = model_dim // num_heads
        self.FC_Q = nn.Linear(model_dim, model_dim)
        self.FC_K = nn.Linear(model_dim, model_dim)
        self.FC_V = nn.Linear(model_dim, model_dim)
        self.out_proj = nn.Linear(model_dim, model_dim)

    def forward(self, query, key, value):
        batch_size = query.shape[0]
        tgt_length = query.shape[-2]
        src_length = key.shape[-2]
        query = self.FC_Q(query)
        key = self.FC_K(key)
        value = self.FC_V(value)
        query = torch.cat(torch.split(query, self.head_dim, dim=-1), dim=0)
        key = torch.cat(torch.split(key, self.head_dim, dim=-1), dim=0)
        value = torch.cat(torch.split(value, self.head_dim, dim=-1), dim=0)
        key = key.transpose(-1, -2)
        attn_score = (query @ key) / self.head_dim**0.5
        if self.mask:
            mask = torch.ones(tgt_length, src_length, dtype=torch.bool, device=query.device).tril()
            attn_score.masked_fill_(~mask, -torch.inf)
        attn_score = torch.softmax(attn_score, dim=-1)
        out = attn_score @ value
        out = torch.cat(torch.split(out, batch_size, dim=0), dim=-1)
        out = self.out_proj(out)
        return out


class SelfAttentionLayer(nn.Module):
    def __init__(self, model_dim, feed_forward_dim=2048, num_heads=8, dropout=0, mask=False):
        super().__init__()
        self.attn = AttentionLayer(model_dim, num_heads, mask)
        self.feed_forward = nn.Sequential(
            nn.Linear(model_dim, feed_forward_dim),
            nn.ReLU(inplace=True),
            nn.Linear(feed_forward_dim, model_dim),
        )
        self.ln1 = nn.LayerNorm(model_dim)
        self.ln2 = nn.LayerNorm(model_dim)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, dim=-2):
        x = x.transpose(dim, -2)
        residual = x
        out = self.attn(x, x, x)
        out = self.dropout1(out)
        out = self.ln1(residual + out)
        residual = out
        out = self.feed_forward(out)
        out = self.dropout2(out)
        out = self.ln2(residual + out)
        out = out.transpose(dim, -2)
        return out


class STAEformer(nn.Module):
    def __init__(
        self,
        num_nodes,
        in_steps=12,
        out_steps=12,
        steps_per_day=288,
        input_dim=3,
        output_dim=1,
        input_embedding_dim=24,
        tod_embedding_dim=24,
        dow_embedding_dim=24,
        spatial_embedding_dim=0,
        adaptive_embedding_dim=80,
        feed_forward_dim=256,
        num_heads=4,
        num_layers=3,
        dropout=0.1,
        use_mixed_proj=True,
    ):
        super().__init__()
        self.num_nodes = num_nodes
        self.in_steps = in_steps
        self.out_steps = out_steps
        self.steps_per_day = steps_per_day
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.input_embedding_dim = input_embedding_dim
        self.tod_embedding_dim = tod_embedding_dim
        self.dow_embedding_dim = dow_embedding_dim
        self.spatial_embedding_dim = spatial_embedding_dim
        self.adaptive_embedding_dim = adaptive_embedding_dim
        self.model_dim = (
            input_embedding_dim + tod_embedding_dim + dow_embedding_dim 
            + spatial_embedding_dim + adaptive_embedding_dim
        )
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.use_mixed_proj = use_mixed_proj

        self.input_proj = nn.Linear(input_dim, input_embedding_dim)
        if tod_embedding_dim > 0:
            self.tod_embedding = nn.Embedding(steps_per_day, tod_embedding_dim)
        if dow_embedding_dim > 0:
            self.dow_embedding = nn.Embedding(7, dow_embedding_dim)
        if spatial_embedding_dim > 0:
            self.node_emb = nn.Parameter(torch.empty(self.num_nodes, spatial_embedding_dim))
            nn.init.xavier_uniform_(self.node_emb)
        if adaptive_embedding_dim > 0:
            self.adaptive_embedding = nn.init.xavier_uniform_(
                nn.Parameter(torch.empty(in_steps, num_nodes, adaptive_embedding_dim))
            )

        if use_mixed_proj:
            self.output_proj = nn.Linear(in_steps * self.model_dim, out_steps * output_dim)
        else:
            self.temporal_proj = nn.Linear(in_steps, out_steps)
            self.output_proj = nn.Linear(self.model_dim, self.output_dim)

        self.attn_layers_t = nn.ModuleList(
            [SelfAttentionLayer(self.model_dim, feed_forward_dim, num_heads, dropout) 
             for _ in range(num_layers)]
        )
        self.attn_layers_s = nn.ModuleList(
            [SelfAttentionLayer(self.model_dim, feed_forward_dim, num_heads, dropout) 
             for _ in range(num_layers)]
        )

    def forward(self, x):
        batch_size = x.shape[0]
        if self.tod_embedding_dim > 0:
            tod = x[..., 1]
        if self.dow_embedding_dim > 0:
            dow = x[..., 2]
        x = x[..., : self.input_dim]
        x = self.input_proj(x)
        features = [x]
        if self.tod_embedding_dim > 0:
            tod_emb = self.tod_embedding((tod * self.steps_per_day).long())
            features.append(tod_emb)
        if self.dow_embedding_dim > 0:
            dow_emb = self.dow_embedding(dow.long())
            features.append(dow_emb)
        if self.spatial_embedding_dim > 0:
            spatial_emb = self.node_emb.expand(batch_size, self.in_steps, *self.node_emb.shape)
            features.append(spatial_emb)
        if self.adaptive_embedding_dim > 0:
            adp_emb = self.adaptive_embedding.expand(size=(batch_size, *self.adaptive_embedding.shape))
            features.append(adp_emb)
        x = torch.cat(features, dim=-1)

        for attn in self.attn_layers_t:
            x = attn(x, dim=1)
        for attn in self.attn_layers_s:
            x = attn(x, dim=2)

        if self.use_mixed_proj:
            out = x.transpose(1, 2)
            out = out.reshape(batch_size, self.num_nodes, self.in_steps * self.model_dim)
            out = self.output_proj(out).view(batch_size, self.num_nodes, self.out_steps, self.output_dim)
            out = out.transpose(1, 2)
        else:
            out = x.transpose(1, 3)
            out = self.temporal_proj(out)
            out = self.output_proj(out.transpose(1, 3))
        return out


def analyze_model_structure():
    print("=" * 60)
    print("STAEformer Model Structure Analysis")
    print("=" * 60)
    
    datasets_config = {
        'METRLA': {'num_nodes': 207, 'in_steps': 12, 'out_steps': 12},
        'PEMSBAY': {'num_nodes': 325, 'in_steps': 12, 'out_steps': 12},
        'PEMS04': {'num_nodes': 307, 'in_steps': 12, 'out_steps': 12},
        'PEMS07': {'num_nodes': 883, 'in_steps': 12, 'out_steps': 12},
        'PEMS08': {'num_nodes': 170, 'in_steps': 12, 'out_steps': 12},
    }
    
    for name, cfg in datasets_config.items():
        print(f"\n[{name}]")
        model = STAEformer(**cfg)
        
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        print(f"  Nodes: {cfg['num_nodes']}")
        print(f"  Model Dim: {model.model_dim}")
        print(f"  Total Params: {total_params:,}")
        print(f"  Trainable Params: {trainable_params:,}")
        
        print(f"  Embedding Params:")
        print(f"    - input_proj: {sum(p.numel() for p in model.input_proj.parameters()):,}")
        print(f"    - tod_embedding: {sum(p.numel() for p in model.tod_embedding.parameters()):,}")
        print(f"    - dow_embedding: {sum(p.numel() for p in model.dow_embedding.parameters()):,}")
        print(f"    - adaptive_embedding: {model.adaptive_embedding.numel():,}")
        
        seq_len = cfg['in_steps']
        num_nodes = cfg['num_nodes']
        model_dim = model.model_dim
        
        t_attn_complexity = seq_len * seq_len * model_dim
        s_attn_complexity = num_nodes * num_nodes * model_dim
        
        print(f"  Attention Complexity (single layer):")
        print(f"    - Temporal: O(T^2 x D) = {t_attn_complexity:,}")
        print(f"    - Spatial: O(N^2 x D) = {s_attn_complexity:,}")
        print(f"    - Total: {t_attn_complexity + s_attn_complexity:,}")
        
        total_complexity = 6 * (t_attn_complexity + s_attn_complexity)
        print(f"  Total 6-layer Complexity: {total_complexity:,}")
    
    return datasets_config


def analyze_embedding_mechanism():
    print("\n" + "=" * 60)
    print("Adaptive Embedding Mechanism Analysis")
    print("=" * 60)
    
    in_steps = 12
    num_nodes = 207
    adaptive_dim = 80
    
    adaptive_params = in_steps * num_nodes * adaptive_dim
    print(f"\n[METRLA Adaptive Embedding]")
    print(f"  Shape: ({in_steps}, {num_nodes}, {adaptive_dim})")
    print(f"  Params: {adaptive_params:,}")
    print(f"  This is a learnable time-space matrix")
    print(f"  Each time step and each node has 80-dim representation")
    
    print(f"\n[Comparison: Static Spatial Embedding]")
    static_spatial = num_nodes * adaptive_dim
    print(f"  Static spatial embedding: {num_nodes} x {adaptive_dim} = {static_spatial:,}")
    print(f"  STAEformer is {adaptive_params / static_spatial:.1f}x of static")
    
    print(f"\n[Temporal vs Spatial Attention]")
    t_attn = in_steps ** 2 * 152
    s_attn = num_nodes ** 2 * 152
    print(f"  Temporal attention matrix: {in_steps} x {in_steps} = {in_steps**2}")
    print(f"  Spatial attention matrix: {num_nodes} x {num_nodes} = {num_nodes**2}")
    print(f"  Temporal attention computation: {t_attn:,}")
    print(f"  Spatial attention computation: {s_attn:,}")
    print(f"  Spatial/Temporal ratio: {s_attn/t_attn:.1f}x")


def analyze_attention_patterns():
    print("\n" + "=" * 60)
    print("Attention Pattern Analysis")
    print("=" * 60)
    
    print("""
[STAEformer Attention Mechanism Features]

1. Separated Spatio-Temporal Attention
   - Temporal attention: self-attention on time dimension (in_steps)
   - Spatial attention: self-attention on node dimension (num_nodes)
   - Alternating: T -> S -> T -> S -> T -> S

2. Attention Computation
   - Standard Scaled Dot-Product Attention
   - Q, K, V linear transformations
   - Complexity: O(L^2 x D) where L is sequence length

3. Comparison with Graph Attention Network
   - GAT: Graph-structured sparse attention O(E x D)
   - STAEformer: Full attention O(N^2 x D) or O(T^2 x D)
   - Advantage: Can capture correlations between arbitrary nodes
   - Disadvantage: Cannot leverage sparsity of graph structure
""")


def simulate_attention_scores():
    print("\n" + "=" * 60)
    print("Attention Score Simulation (METRLA)")
    print("=" * 60)
    
    batch_size = 2
    in_steps = 12
    num_nodes = 207
    model_dim = 152
    num_heads = 4
    head_dim = model_dim // num_heads
    
    x = torch.randn(batch_size, in_steps, num_nodes, model_dim)
    
    FC_Q = nn.Linear(model_dim, model_dim)
    FC_K = nn.Linear(model_dim, model_dim)
    FC_V = nn.Linear(model_dim, model_dim)
    
    Q = FC_Q(x)
    K = FC_K(x)
    V = FC_V(x)
    
    print(f"\nInput shape: {x.shape}")
    print(f"Q/K/V shape: {Q.shape}")
    
    Q_t = Q.transpose(1, 2)
    K_t = K.transpose(1, 2)
    V_t = V.transpose(1, 2)
    
    Q_s = Q
    K_s = K
    V_s = V
    
    print(f"\n[Temporal Attention]")
    print(f"  Q_t shape: {Q_t.shape} (B, N, T, D)")
    print(f"  K_t shape: {K_t.shape}")
    print(f"  Attention matrix: {in_steps} x {in_steps} = {in_steps**2}")
    print(f"  Per-head computation: {in_steps}^2 x {head_dim} = {in_steps**2 * head_dim}")
    print(f"  Total temporal attention: {batch_size * num_nodes * in_steps**2 * head_dim * num_heads:,}")
    
    print(f"\n[Spatial Attention]")
    print(f"  Q_s shape: {Q_s.shape} (B, T, N, D)")
    print(f"  K_s shape: {K_s.shape}")
    print(f"  Attention matrix: {num_nodes} x {num_nodes} = {num_nodes**2}")
    print(f"  Per-head computation: {num_nodes}^2 x {head_dim} = {num_nodes**2 * head_dim}")
    print(f"  Total spatial attention: {batch_size * in_steps * num_nodes**2 * head_dim * num_heads:,}")
    
    t_calc = batch_size * num_nodes * in_steps**2 * head_dim * num_heads
    s_calc = batch_size * in_steps * num_nodes**2 * head_dim * num_heads
    print(f"\n[Computation Comparison]")
    print(f"  Temporal attention: {t_calc:,}")
    print(f"  Spatial attention: {s_calc:,}")
    print(f"  Spatial/Temporal ratio: {s_calc/t_calc:.1f}x")


def load_and_analyze_data():
    print("\n" + "=" * 60)
    print("Dataset Analysis")
    print("=" * 60)
    
    import os
    
    data_dir = "data/METRLA"
    if os.path.exists(os.path.join(data_dir, "data.npz")):
        data = np.load(os.path.join(data_dir, "data.npz"))
        index = np.load(os.path.join(data_dir, "index.npz"))
        
        traffic_data = data['data']
        print(f"\n[METRLA Dataset]")
        print(f"  Data shape: {traffic_data.shape}")
        print(f"  (time_steps, nodes, features)")
        print(f"  Time steps: {traffic_data.shape[0]}")
        print(f"  Nodes: {traffic_data.shape[1]}")
        print(f"  Feature dim: {traffic_data.shape[2]}")
        print(f"  Features: [traffic_flow, time_of_day, day_of_week]")
        
        traffic_flow = traffic_data[..., 0]
        print(f"\n  Traffic flow statistics:")
        print(f"    Min: {traffic_flow.min():.4f}")
        print(f"    Max: {traffic_flow.max():.4f}")
        print(f"    Mean: {traffic_flow.mean():.4f}")
        print(f"    Std: {traffic_flow.std():.4f}")
        
        train_idx = index['train']
        val_idx = index['val']
        test_idx = index['test']
        
        print(f"\n  Dataset split:")
        print(f"    Train samples: {len(train_idx)}")
        print(f"    Val samples: {len(val_idx)}")
        print(f"    Test samples: {len(test_idx)}")
        print(f"    Total: {len(train_idx) + len(val_idx) + len(test_idx)}")
        
        sample_len = 12
        pred_len = 12
        total_window = sample_len + pred_len
        
        print(f"\n  Time window:")
        print(f"    Input length: {sample_len} steps")
        print(f"    Prediction length: {pred_len} steps")
        print(f"    Total window: {total_window} steps")
        print(f"    About: {total_window * 5 / 60:.1f} hours (5 min/step)")
    else:
        print(f"\n  Data file not found: {os.path.join(data_dir, 'data.npz')}")


def problem_analysis():
    print("\n" + "=" * 60)
    print("STAEformer Problem Analysis")
    print("=" * 60)
    
    print("""
[1. Computational Complexity Problem]
   
   Issue: Spatial attention complexity O(N^2 x D) is very high for large-scale road networks
   - METRLA (N=207): 207^2 = 42,849
   - PEMS07 (N=883): 883^2 = 779,689
   - Larger networks face serious computation and memory issues

   Solutions:
   - Sparse attention mechanisms (Swin Transformer)
   - Local spatial attention + global aggregation
   - Graph structure-guided sparse attention

[2. Limitations of Separated Spatio-Temporal Attention]

   Issue: Alternating spatio-temporal attention cannot capture fine-grained spatio-temporal interactions
   - Temporal attention first, then spatial attention
   - Or vice versa
   - Loses joint time-space modeling

   Solutions:
   - Joint spatio-temporal attention (like 3D convolution)
   - Spatio-temporal graph attention networks
   - Cross-attention mechanism

[3. Redundancy in Adaptive Embedding]

   Issue: Adaptive embedding matrix (T x N x D) may have significant redundancy
   - All time steps share similar patterns
   - Does not consider dependencies at different time scales

   Solutions:
   - Multi-scale adaptive embedding
   - Hierarchical temporal embedding
   - Periodic-aware embedding

[4. Limitations of Position Encoding]

   Issue: Only using Time-of-Day and Day-of-Week encoding
   - Lack of finer-grained temporal information
   - Cannot capture holidays, events, etc.

   Solutions:
   - Add holiday encoding
   - Event-aware embedding
   - Periodic position encoding

[5. Lack of Graph Structure Priors]

   Issue: Completely discards road network graph structure information
   - Does not leverage physical connections between sensors
   - Treats all node pairs equally

   Solutions:
   - Graph structure-guided attention bias
   - Geographic information fusion
   - Distance decay attention

[6. Limited Long-term Prediction Capability]

   Issue: 12-step prediction (1 hour) may not be enough for some applications
   - Model mainly designed for short-to-medium term prediction
   - Longer predictions require more complex mechanisms

   Solutions:
   - Hierarchical prediction (multi-scale)
   - Recursive refinement prediction
   - Diffusion models for long-term prediction
""")


def improvement_suggestions():
    print("\n" + "=" * 60)
    print("Improvement Suggestions Summary")
    print("=" * 60)
    
    print("""
[Improvement Directions]

1. Efficiency Improvement
   |- Local sparse attention (LogSparse, Longformer style)
   |- Hierarchical spatial modeling (like Swin)
   |- Linear attention mechanism (Performer, Linformer)
   |- Knowledge distillation compression

2. Spatio-Temporal Modeling Enhancement
   |- Joint spatio-temporal attention
   |- Multi-scale temporal modeling
   |- Periodic-aware mechanism
   |- External event fusion

3. Graph Structure Integration
   |- Graph-guided attention bias
   |- Geographic distance encoding
   |- Graph convolution enhancement

4. Prediction Capability Extension
   |- Multi-task learning (short + long term)
   |- Uncertainty quantification
   |- Distribution prediction (not just point prediction)

5. Interpretability Enhancement
   |- Attention visualization analysis
   |- Key node identification
   |- Prediction explanation analysis
""")


if __name__ == "__main__":
    datasets_config = analyze_model_structure()
    analyze_embedding_mechanism()
    analyze_attention_patterns()
    simulate_attention_scores()
    load_and_analyze_data()
    problem_analysis()
    improvement_suggestions()
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
