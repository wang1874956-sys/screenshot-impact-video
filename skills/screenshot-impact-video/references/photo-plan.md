# 通用照片配置

创建项目：

```sh
python scripts/scaffold.py --source photo.jpg --output output/photo-demo --template photo --intensity strong --camera dynamic --duration 18 --fps 30
```

命令路径相对于 Skill。生成的 motion-plan.json 由 photo 构建器实际读取。出片前仍须按用户图片构图调整。cards/icons 的配置采用各自 build.py，不支持在此 JSON 中自动重排原模板。

## 参数

- `source.file`、`width`、`height`、`orientation`：创建器读取的源图信息；不要只改数字假装已旋转图片。
- `output.width/height`：2–4096 之间的偶整数；默认按源图原生尺寸，奇数边只补 1 像素。源图超过本模板 4096 像素上限时创建器报错，不自动缩小。
- `output.duration`：2–60 秒；`fps`：1–60 整数。构建时同步 npm render 的帧率。
- `style.intensity`：subtle / balanced / strong，实际影响图层位移、旋转和默认镜头力度。
- `style.camera`：static / cinematic / dynamic。static 保持镜头不动；仍可有独立图层动画。
- `style.sound`：true / false。false 时 HTML 不挂载音轨。`seed` 固定合成音效的随机序列。
- `style.focus`：可选 `[0到1,0到1]` 归一化焦点；未指定时优先选择第一个图层的中心。
- `layers`：人工定义的截图/照片裁切图层。空列表只做镜头运动。
- `patches`：已有辅助背景图的局部合成。构建器不会自己生成辅助图。
- `lights`：局部光效脉冲，按指定矩形添加光晕，不会模拟真实照明或重画物体。

## 一个图层

以下仅为字段示例，坐标必须来自实际图片；选区不能越出原图：

```json
{
  "id": "subject-1",
  "rect": [300, 500, 180, 140],
  "polygon": [[310, 500], [460, 510], [480, 620], [320, 640], [300, 580]],
  "start": 3,
  "move_duration": 0.7,
  "dx": -50,
  "dy": -150,
  "rotation": -12,
  "scale": 1.15
}
```

rect 为 `[x,y,width,height]`；polygon 是可选的原图像素坐标，不是相对 rect 的坐标。应包住整个主体，同时避免带入多余背景。动画后段自动将图层归位。多边形适合边缘清楚的物体；毛发、曲线、反光物体优先使用带透明度的 PNG 裁片。

真实物体的透明裁片可以用 `"cutout": "subject.png"` 替代 `polygon`。PNG 必须有 alpha 通道，宽高等于 `rect` 的宽高，内容与原图坐标精确对应；构建器会拒绝尺寸不符或无 alpha 的文件。模板不会生成抠图，必须逐张检查毛发、反光、透视和图层移动后的边缘。透明裁片仍需与背景补片配对，不能让原主体在底图中形成重影。

## 背景补片

```json
{"file": "clean-plate.png", "rect": [290, 490, 210, 180], "start": 2.9}
```

辅助底图应与原图同构图，构建器按原图尺寸适配其显示大小；rect 使用原图坐标。先查看修复区域与原图对齐情况。矩形补片边缘不够自然时，添加 `"mask": "patch-mask.png"`：这是与**整张源图同尺寸**的 RGBA PNG，透明区域不显示补片，主体原位置及周围用平滑 alpha 过渡。模板会检查尺寸与 alpha 格式，但不会自动生成蒙版或判断修复内容是否可信。所有辅助素材必须放在输出项目中，不能引用项目外的私人文件。

## 边界保护

局部光效示例，坐标必须适配原图：

```json
{"rect": [600, 800, 400, 500], "color": "#bd5dff", "opacity": 0.4, "start": 5, "duration": 2}
```

把它加入 lights 数组。光晕使用 screen 混合，在指定时段渐强后衰减，末尾恢复原图。

默认镜头在关键姿态下计算最小缩放与位移限制，防止旋转后露出照片边缘。代理仍需检查过渡中间帧，尤其是改写默认时间线以后。原图比例与输出画幅不同时，stage 之外的设计留边不属于意外露底。
