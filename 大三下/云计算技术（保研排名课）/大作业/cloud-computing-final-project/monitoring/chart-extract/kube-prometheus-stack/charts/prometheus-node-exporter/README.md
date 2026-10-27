# prometheus-node-exporter

<!-- directory-guide:start -->
## 本层内容介绍

这里是“云计算技术”课程下的“prometheus-node-exporter”目录，主要用于整理该主题的配套文件或下级模块。

**阅读建议：**先看下方内容摘要选择入口；需要了解整体任务时返回上级项目或课程说明。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **17 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

| 子目录 | 内容与用途 |
| --- | --- |
| [templates](templates/README.md) | 页面、配置或文档模板 |

- **配置及其他配套文件（3 份）**：[.helmignore](.helmignore)、[Chart.yaml](Chart.yaml)等；完整列表见本页导航。

<!-- directory-guide:end -->

所属课程：[云计算技术](../../../../../../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [templates/](templates/README.md)
- [.helmignore](.helmignore)
- [Chart.yaml](Chart.yaml)
- [values.yaml](values.yaml)

[返回上级目录](../README.md)

## 原有项目说明

# Prometheus Node Exporter

Prometheus exporter for hardware and OS metrics exposed by *NIX kernels, written in Go with pluggable metric collectors.

This chart bootstraps a Prometheus [Node Exporter](http://github.com/prometheus/node_exporter) daemonset on a [Kubernetes](http://kubernetes.io) cluster using the [Helm](https://helm.sh) package manager.

## Usage

The chart is distributed as an [OCI Artifact](https://helm.sh/docs/topics/registries/) as well as via a traditional [Helm Repository](https://helm.sh/docs/topics/chart_repository/).

- OCI Artifact: `oci://ghcr.io/prometheus-community/charts/prometheus-node-exporter`
- Helm Repository: `https://prometheus-community.github.io/helm-charts` with chart `prometheus-node-exporter`

The installation instructions use the OCI registry. Refer to the [`helm repo`]([`helm repo`](https://helm.sh/docs/helm/helm_repo/)) command documentation for information on installing charts via the traditional repository.

### Install Chart

```console
helm install [RELEASE_NAME] oci://ghcr.io/prometheus-community/charts/prometheus-node-exporter
```

_See [configuration](#configuring) below._

_See [helm install](https://helm.sh/docs/helm/helm_install/) for command documentation._

### Uninstall Chart

```console
helm uninstall [RELEASE_NAME]
```

This removes all the Kubernetes components associated with the chart and deletes the release.

_See [helm uninstall](https://helm.sh/docs/helm/helm_uninstall/) for command documentation._

### Upgrading Chart

```console
helm upgrade [RELEASE_NAME] oci://ghcr.io/prometheus-community/charts/prometheus-node-exporter --install
```

_See [helm upgrade](https://helm.sh/docs/helm/helm_upgrade/) for command documentation._

#### 3.x to 4.x

Starting from version 4.0.0, the `node exporter` chart is using the [Kubernetes recommended labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/). Therefore you have to delete the daemonset before you upgrade.

```console
kubectl delete daemonset -l app=prometheus-node-exporter
helm upgrade -i prometheus-node-exporter prometheus-community/prometheus-node-exporter
```

If you use your own custom [ServiceMonitor](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/api-reference/api.md#servicemonitor) or [PodMonitor](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/api-reference/api.md#podmonitor), please ensure to upgrade their `selector` fields accordingly to the new labels.

#### From 2.x to 3.x

Change the following:

```yaml
hostRootFsMount: true
```

to:

```yaml
hostRootFsMount:
  enabled: true
  mountPropagation: HostToContainer
```

## Configuring

See [Customizing the Chart Before Installing](https://helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing). To see all configurable options with detailed comments, visit the chart's [values.yaml](values.yaml), or run these configuration commands:

```console
helm show values oci://ghcr.io/prometheus-community/charts/prometheus-node-exporter
```

### kube-rbac-proxy

You can enable `prometheus-node-exporter` endpoint protection using `kube-rbac-proxy`. By setting `kubeRBACProxy.enabled: true`, this chart will deploy a RBAC proxy container protecting the node-exporter endpoint.
To authorize access, authenticate your requests (via a `ServiceAccount` for example) with a `ClusterRole` attached such as:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus-node-exporter-read
rules:
  - apiGroups: [ "" ]
    resources: ["services/node-exporter-prometheus-node-exporter"]
    verbs:
      - get
```

See [kube-rbac-proxy examples](https://github.com/brancz/kube-rbac-proxy/tree/master/examples/resource-attributes) for more details.

