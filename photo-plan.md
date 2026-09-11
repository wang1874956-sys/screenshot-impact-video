# 通用照片配置

创建项目：

```sh
python scripts/scaffold.py --source photo.jpg --output output/photo-demo --template photo --intensity strong --camera dynamic --duration 18 --fps 30
```

命令路径相对于 Skill。生成的 motion-plan.json 由 photo 构建器实际读取。出片前仍须按用户图片构图调整。cards/icons 的配置采用各自 build.py，不支持在此 JSON 中自动重排原模板。

## 参数

- `source.file`、`width`、`height`、`orientation`：创建器读取的源图信息；不要只改数字假装已旋转图片。
- `output.width/height`：2–4096 之间的偶整数；默认原图比例、宽 1080。极端高宽比限制输出高度为 4096，使用居中留边保护整图。
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

rect 为 `[x,y,width,height]`；polygon 是可选的原图像素坐标，不是相对 rect 的坐标。应包住整个主体，同时避免带入多余背景。动画后段自动将图层归位。

## 背景补片

```json
{"file": "clean-plate.png", "rect": [290, 490, 210, 180], "start": 2.9}
```

辅助底图应与原图同构图，构建器按原图尺寸适配其显示大小；rect 使用原图坐标。先查看修复区域与原图对齐情况。矩形补片边缘不够自然时，应在项目中进一步做蒙版与过渡，而不是交付明显接缝。所有辅助素材必须放在输出项目中，不能引用项目外的私人文件。

## 边界保护

局部光效示例，坐标必须适配原图：

```json
{"rect": [600, 800, 400, 500], "color": "#bd5dff", "opacity": 0.4, "start": 5, "duration": 2}
```

把它加入 lights 数组。光晕使用 screen 混合，在指定时段渐强后衰减，末尾恢复原图。

默认镜头在关键姿态下计算最小缩放与位移限制，防止旋转后露出照片边缘。代理仍需检查过渡中间帧，尤其是改写默认时间线以后。原图比例与输出画幅不同时，stage 之外的设计留边不属于意外露底。
