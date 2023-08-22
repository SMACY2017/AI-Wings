
## Meterials

| Item                                              | Number |
| ------------------------------------------------- | ------ |
| 展示架+背景布                                     | 1      |
| microUSB数据线2m                                  | 4      |
| USB充电插头                                       | 4      |
| USB延长线                                         | 2      |
| Jetson亚克力外壳/无线网卡/充电器/跳线帽/风扇/SD卡 | 2      |
| Jetson Nano                                       | 1      |
| Arduino Mega 2560 + 线                            | 1      |
| 灯带（盘）                                        | 2      |
| 电烙铁+焊锡                                       | 1      |
| 轧带（捆）                                        | 2      |
| 7存HDMI显示屏                                     | 1      |
| HDMI数据线2m                                      | 1      |
| USB外接摄像头                                     | 1      |
| 木工胶水（升）                                    | 1      |
| 插线板2m   5孔位                                  | 1      |
| 红外热释电人体传感器                              | 1      |
| 双公头/母转公杜邦线                               | 10     |
| 热熔胶胶枪+10根胶棒                               | 1      |
| 螺丝钉/螺丝刀/剥线钳/老虎钳                       | 1      |
| 细铁丝                                            | 1      |
| 卷尺                                              | 1      |
| 硬纸板                                            | 2      |

## Technical Details

#### Jetson Nano 烧写镜像

> 全文参考 [Get Started With Jetson Nano Developer Kit | NVIDIA Developer](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#write)

1. 下载[镜像文件](https://developer.nvidia.com/jetson-nano-sd-card-image)
2. 安装镜像烧录工具[Etcher](https://www.balena.io/etcher)
3. 选择下载的镜像，以及插入至少32GB的SD卡，烧写镜像

   <img src="./assets/Jetson_Nano-Getting_Started-Windows-Etcher_Select_Drive.png" alt="Jetson_Nano-Getting_Started-Windows-Etcher_Select_Drive" style="zoom: 80%;" />

#### Jetson Nano 开机和基本配置

**推荐使用5V 4A以上的DC电源，为了后续运行的电源消耗**

1. 使用跳线帽，短接 Jetson 主板上的 J48 引脚，确保使用DC供电模式

<img src="./assets/20201225133627579.png" alt="20201225133627579" style="zoom:10%;" />

2. 连接HDMI显示屏，以及键鼠，正常开机进入Ubuntu系统，按照提示完成基本设置。
3. 为了后续运行模型需要，**推荐安装一个PWM 4pin的风扇**。关于风扇调速的设置可以参考https://github.com/Pyrestone/jetson-fan-ctl

#### Jetson Nano环境搭建

1. 安装Conda环境：

   前往 https://github.com/Archiconda/build-tools/releases下载 Archiconda 脚本，直接运行安装

   ```bash
   chmod 777 Archiconda3-0.2.3-Linux-aarch64.sh
   ./Archiconda3-0.2.3-Linux-aarch64.sh
   ```
2. 前往[paddle官方](https://paddleinference.paddlepaddle.org.cn/user_guides/download_lib.html#python)下载编译好的包，对于 Jetson nano ，选择 `paddlepaddle_gpu-2.3.2-cp37-cp37m-linux_aarch64.whl`
3. 创建并配置环境、增加虚拟内存swap空间：

   ```bash
   # 创建paddle37虚拟环境
   conda create -n paddle37 python=3.7
   conda activate paddle37
   # 安装刚刚下载的paddle whl包，以及其他依赖
   pip3 install paddlepaddle_gpu-2.3.2-cp37-cp37m-linux_aarch64.whl
   ```

   ```bash
   sudo fallocate -l 8G /var/swapfile8G
   sudo chmod 600 /var/swapfile8G
   sudo mkswap /var/swapfile8G
   sudo swapon /var/swapfile8G
   sudo bash -c 'echo "/var/swapfile8G swap swap defaults 0 0" >> /etc/fstab'
   ```
4. 安装PaddleDetecttion并导出yolo模型

   > 比如在~/Desktop/workspace/目录下
   >

   ```bash
   git clone https://github.com/PaddlePaddle/PaddleDetection.git
   # 目录下会出现PaddleDetection文件夹
   mkdir -p pyyoloe/inference_model #创建存放导出模型的文件夹
   cd ./PaddleDetection #切换到对应目录
   pip install pyserial #安装相关依赖
   pip install -r requirements.txt #安装paddledetection的依赖
   # 导出模型
   python tools/export_model.py -c configs/ppyoloe/ppyoloe_plus_crn_t_auxhead_320_300e_coco.yml --output_dir=./inference_model \
                                 -o weights=https://paddledet.bj.bcebos.com/models/ppyoloe_plus_crn_t_auxhead_320_300e_coco.pdparams trt=True
   ```
5. 赋予串口 `/tty/ACM0`读写权限，用于和 Arduino 通信

   ```bash
   # navigate to rules.d directory
   cd /etc/udev/rules.d
   #create a new rule file
   sudo touch my-newrule.rules
   # open the file
   sudo vim my-newrule.rules
   ```

   在 `my-newrule.rules`中填入以下内容

   ```json
   KERNEL=="ttyACM0", MODE="0666"
   ```

   **最后重启**，完成环境搭建

#### Arduino Mega 2560 配置

1. 电脑下载并安装 [Arduino IDE](https://www.arduino.cc/en/software)
2. 打开Arduino IDE，选择 `Tools` - `Manage Libraries`

   搜索并安装 `FastLED`组件
3. 将 Arduino Mega2560 使用USB连接到电脑，烧录程序 `./code/LED_with_human.ino`

   *(根据灯带的部署情况，代码可能需要进行微调)*

### Arduino Mega 2560 接线

<img src="./assets/Arduino-Mega-Pinout.png" alt="Arduino-Mega-Pinout" style="zoom: 30%;" />

1. 将USB连接到 Jetson Nano主板上
2. 灯带的信号控制线连接 `6 引脚`，热释电模块连接到 `7 引脚`
3. 将灯带的供电和热释电模块的供电线（一般为红色，标记 Vcc）连接到主板 `5V 引脚`或者 `Vin 引脚`。
4. 将灯带的接地和热释电模块的接地（一般为黑色，标记 GND）连接到主板 `GND 引脚`。
5. 在灯带的开头，中间段，以及末尾提供USB供电

#### 在Jetson Nano中设置开机自启

1. 创建start.sh文件

   ```bash
   # 激活对应的虚拟环境，有可能直接使用conda activate不起作用，使用which conda命令找到安装的位置
   # 例如which conda结果为/home/garage/miniforge3/bin/conda，那么source命令如下
   # source /home/garage/miniforge3/etc/profile.d/conda.sh
   conda activate paddle37

   cd /home/garage/Desktop/workspace/
   python maine_with_human_test.py
   ```
2. 确保脚本是可执行的

   ```bash
   chmod +x /path/to/start.sh
   ```
4. 将start.sh文件打包成桌面启动器文件

   - 创建一个桌面启动器
     创建一个名为 `start.desktop`的新文件在你的桌面或其他位置：

   ```bash
   vim ~/Desktop/start.desktop
   ```

   然后，将以下内容粘贴到该文件中：

   ```ini
   [Desktop Entry]
   Name=Start My Project
   Comment=Run my start.sh script
   Exec=gnome-terminal -- bash -c "/path/to/start.sh; exec bash"
   Icon=terminal
   Terminal=false
   Type=Application
   ```

   请确保替换 `/path/to/start.sh`为你的 `start.sh`脚本的绝对路径。

   - 使桌面启动器可执行

   与脚本一样，确保桌面启动器文件也是可执行的：

   ```bash
   chmod +x ~/Desktop/start.desktop
   ```

   现在，你应该在桌面上看到一个名为“Start My Project”的图标。双击它会打开一个终端并运行你的 `start.sh`脚本。
5. 设置开机自启

   在Linux中，桌面启动器（`.desktop`文件）可以用于开机自启动，只需将其放置在 `~/.config/autostart/`目录下。但请注意，这种方法只在启动图形用户界面（如GNOME、KDE等）时有效，如果你的Jetson Nano没有启动图形界面，这种方法可能不会工作。

   以下是如何设置 `start.desktop`以使其在开机时自动启动的步骤：

   1. **确保 `~/.config/autostart/`目录存在**:

      如果该目录不存在，你需要创建它：

      ```bash
      mkdir -p ~/.config/autostart/
      ```
   2. **复制或链接你的桌面启动器到该目录**:

      ```bash
      cp /path/to/start.desktop ~/.config/autostart/
      ```

      或者

      ```bash
      ln -s /path/to/start.desktop ~/.config/autostart/
      ```
   3. **重启**:

      重启你的Jetson Nano，然后检查是否在桌面环境启动时自动运行了你的脚本。
