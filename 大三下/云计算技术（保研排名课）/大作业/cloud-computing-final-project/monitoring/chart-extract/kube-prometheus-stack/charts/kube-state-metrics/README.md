# kube-state-metrics

<!-- directory-guide:start -->
## 本层内容介绍

这里是“云计算技术”课程下的“kube-state-metrics”目录，主要用于整理该主题的配套文件或下级模块。

**阅读建议：**先看下方内容摘要选择入口；需要了解整体任务时返回上级项目或课程说明。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **22 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

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

# kube-state-metrics Helm Chart

Installs the [kube-state-metrics agent](https://github.com/kubernetes/kube-state-metrics).

## Usage

The chart is distributed as an [OCI Artifact](https://helm.sh/docs/topics/registries/) as well as via a traditional [Helm Repository](https://helm.sh/docs/topics/chart_repository/).

- OCI Artifact: `oci://ghcr.io/prometheus-community/charts/kube-state-metrics`
- Helm Repository: `https://prometheus-community.github.io/helm-charts` with chart `kube-state-metrics`

The installation instructions use the OCI registry. Refer to the [`helm repo`]([`helm repo`](https://helm.sh/docs/helm/helm_repo/)) command documentation for information on installing charts via the traditional repository.

### Install Chart

```console
helm install [RELEASE_NAME] oci://ghcr.io/prometheus-community/charts/kube-state-metrics [flags]
```

_See [configuration](#configuration) below._

_See [helm install](https://helm.sh/docs/helm/helm_install/) for command documentation._

### Uninstall Chart

```console
helm uninstall [RELEASE_NAME]
```

This removes all the Kubernetes components associated with the chart and deletes the release.

_See [helm uninstall](https://helm.sh/docs/helm/helm_uninstall/) for command documentation._

### Upgrading Chart

```console
helm upgrade [RELEASE_NAME] oci://ghcr.io/prometheus-community/charts/kube-state-metrics [flags]
```

_See [helm upgrade](https://helm.sh/docs/helm/helm_upgrade/) for command documentation._

#### Migrating from stable/kube-state-metrics and kubernetes/kube-state-metrics

You can upgrade in-place:

1. [upgrade](#upgrading-chart) your existing release name using the new chart repository

## Upgrading to v6.0.0

This version drops support for deprecated Pod Security Policy resources.

## Upgrading to v3.0.0

v3.0.0 includes kube-state-metrics v2.0, see the [changelog](https://github.com/kubernetes/kube-state-metrics/blob/release-2.0/CHANGELOG.md) for major changes on the application-side.

The upgraded chart now the following changes:

- Dropped support for helm v2 (helm v3 or later is required)
- collectors key was renamed to resources
- namespace key was renamed to namespaces

## Configuration

See [Customizing the Chart Before Installing](https://helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing). To see all configurable options with detailed comments:

```console
helm show values oci://ghcr.io/prometheus-community/charts/kube-state-metrics
```

### kube-rbac-proxy

You can enable `kube-state-metrics` endpoint protection using `kube-rbac-proxy`. By setting `kubeRBACProxy.enabled: true`, this chart will deploy one RBAC proxy container per endpoint (metrics & telemetry).
To authorize access, authenticate your requests (via a `ServiceAccount` for example) with a `ClusterRole` attached such as:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kube-state-metrics-read
rules:
  - apiGroups: [ "" ]
    resources: ["services/kube-state-metrics"]
    verbs:
      - get
```

See [kube-rbac-proxy examples](https://github.com/brancz/kube-rbac-proxy/tree/master/examples/resource-attributes) for more details.

