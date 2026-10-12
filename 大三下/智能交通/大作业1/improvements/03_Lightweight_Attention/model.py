"""
优化方法3：引入轻量化注意力机制
Lightweight Attention Mechanism

设计思路：将原模型的稠密注意力替换为稀疏注意力或线性注意力，
降低大规模交通网络下的计算复杂度。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LinearAttention(nn.Module):
    """线性注意力机制 - 复杂度从O(N²)降低到O(N)"""
    def __init__(self, model_dim, num_heads=8):
        super().__init__()
        self.model_dim = model_dim
        self.num_heads = num_heads
        self.head_dim = model_dim // num_heads
        
        self.FC_Q = nn.Linear(model_dim, model_dim)
        self.FC_K = nn.Linear(model_dim, model_dim)
        self.FC_V = nn.Linear(model_dim, model_dim)
        self.out_proj = nn.Linear(model_dim, model_dim)
        
        self.elu = nn.ELU()
    
    def forward(self, query, key, value):
        batch_size = query.shape[0]
        
        query = self.FC_Q(query)
        key = self.FC_K(key)
        value = self.FC_V(value)
        
        query = torch.cat(torch.split(query, self.head_dim, dim=-1), dim=0)
        key = torch.cat(torch.split(key, self.head_dim, dim=-1), dim=0)
        value = torch.cat(torch.split(value, self.head_dim, dim=-1), dim=0)
        
        query = self.elu(query) + 1
        key = self.elu(key) + 1
        
        key_t = key.transpose(-1, -2)
        kv = key_t @ value
        k_sum = key.sum(dim=-2, keepdim=True)
        
        z = 1.0 / (query @ k_sum.transpose(-1, -2) + 1e-6)
        out = (query @ kv) * z
        
        out = torch.cat(torch.split(out, batch_size, dim=0), dim=-1)
        out = self.out_proj(out)
        
        return out


class SparseAttention(nn.Module):
    """稀疏注意力机制 - 只关注Top-k个最相关的位置"""
    def __init__(self, model_dim, num_heads=8, sparsity_ratio=0.5):
        super().__init__()
        self.model_dim = model_dim
        self.num_heads = num_heads
        self.head_dim = model_dim // num_heads
        self.sparsity_ratio = sparsity_ratio
        
        self.FC_Q = nn.Linear(model_dim, model_dim)
        self.FC_K = nn.Linear(model_dim, model_dim)
        self.FC_V = nn.Linear(model_dim, model_dim)
        self.out_proj = nn.Linear(model_dim, model_dim)
    
    def forward(self, query, key, value):
        batch_size = query.shape[0]
        seq_len = query.shape[-2]
        
        query = self.FC_Q(query)
        key = self.FC_K(key)
        value = self.FC_V(value)
        
        query = torch.cat(torch.split(query, self.head_dim, dim=-1), dim=0)
        key = torch.cat(torch.split(key, self.head_dim, dim=-1), dim=0)
        value = torch.cat(torch.split(value, self.head_dim, dim=-1), dim=0)
        
        key = key.transpose(-1, -2)
        
        attn_score = (query @ key) / self.head_dim**0.5
        
        k = max(1, int(seq_len * self.sparsity_ratio))
        top_k_values, top_k_indices = torch.topk(attn_score, k, dim=-1)
        
        sparse_attn = torch.zeros_like(attn_score)
        sparse_attn.scatter_(-1, top_k_indices, torch.softmax(top_k_values, dim=-1))
        
        out = sparse_attn @ value
        out = torch.cat(torch.split(out, batch_size, dim=0), dim=-1)
        out = self.out_proj(out)
        
        return out


class LightSelfAttentionLayer(nn.Module):
    """轻量化自注意力层"""
    def __init__(
        self, model_dim, feed_forward_dim=2048, num_heads=8, dropout=0, 
        attention_type='linear', sparsity_ratio=0.5
    ):
        super().__init__()
        
        if attention_type == 'linear':
            self.attn = LinearAttention(model_dim, num_heads)
        else:
            self.attn = SparseAttention(model_dim, num_heads, sparsity_ratio)
        
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


class STAEformer_LA(nn.Module):
    """STAEformer with Lightweight Attention"""
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
        attention_type='linear',
        sparsity_ratio=0.5,
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
            input_embedding_dim
            + tod_embedding_dim
            + dow_embedding_dim
            + spatial_embedding_dim
            + adaptive_embedding_dim
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
            self.node_emb = nn.Parameter(
                torch.empty(self.num_nodes, self.spatial_embedding_dim)
            )
            nn.init.xavier_uniform_(self.node_emb)
        if adaptive_embedding_dim > 0:
            self.adaptive_embedding = nn.init.xavier_uniform_(
                nn.Parameter(torch.empty(in_steps, num_nodes, adaptive_embedding_dim))
            )

        if use_mixed_proj:
            self.output_proj = nn.Linear(
                in_steps * self.model_dim, out_steps * output_dim
            )
        else:
            self.temporal_proj = nn.Linear(in_steps, out_steps)
            self.output_proj = nn.Linear(self.model_dim, self.output_dim)

        self.attn_layers_t = nn.ModuleList(
            [
                LightSelfAttentionLayer(
                    self.model_dim, feed_forward_dim, num_heads, dropout,
                    attention_type, sparsity_ratio
                )
                for _ in range(num_layers)
            ]
        )

        self.attn_layers_s = nn.ModuleList(
            [
                LightSelfAttentionLayer(
                    self.model_dim, feed_forward_dim, num_heads, dropout,
                    attention_type, sparsity_ratio
                )
                for _ in range(num_layers)
            ]
        )

    def forward(self, x):
        batch_size = x.shape[0]

        tod = None
        dow = None
        if self.tod_embedding_dim > 0:
            tod = x[..., 1]
        if self.dow_embedding_dim > 0:
            dow = x[..., 2]
        x = x[..., : self.input_dim]

        x = self.input_proj(x)
        features = [x]
        if self.tod_embedding_dim > 0 and tod is not None:
            tod_emb = self.tod_embedding((tod * self.steps_per_day).long())
            features.append(tod_emb)
        if self.dow_embedding_dim > 0 and dow is not None:
            dow_emb = self.dow_embedding(dow.long())
            features.append(dow_emb)
        if self.spatial_embedding_dim > 0:
            spatial_emb = self.node_emb.expand(
                batch_size, self.in_steps, *self.node_emb.shape
            )
            features.append(spatial_emb)
        if self.adaptive_embedding_dim > 0:
            adp_emb = self.adaptive_embedding.expand(
                size=(batch_size, *self.adaptive_embedding.shape)
            )
            features.append(adp_emb)
        x = torch.cat(features, dim=-1)

        for attn in self.attn_layers_t:
            x = attn(x, dim=1)
        for attn in self.attn_layers_s:
            x = attn(x, dim=2)

        if self.use_mixed_proj:
            out = x.transpose(1, 2)
            out = out.reshape(batch_size, self.num_nodes, self.in_steps * self.model_dim)
            out = self.output_proj(out).view(
                batch_size, self.num_nodes, self.out_steps, self.output_dim
            )
            out = out.transpose(1, 2)
        else:
            out = x.transpose(1, 3)
            out = self.temporal_proj(out)
            out = self.output_proj(out.transpose(1, 3))

        return out


if __name__ == "__main__":
    from torchinfo import summary
    model = STAEformer_LA(207, 12, 12, attention_type='linear')
    summary(model, [64, 12, 207, 3])
