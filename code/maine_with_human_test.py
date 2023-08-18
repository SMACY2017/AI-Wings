import cv2
import numpy as np
from paddle.inference import Config
from paddle.inference import PrecisionType
from paddle.inference import create_predictor
from sklearn.cluster import KMeans
import yaml
import time
import serial
import sys
import re


def resize(img, target_size):
    """resize to target size"""
    if not isinstance(img, np.ndarray):
        raise TypeError('image type is not numpy.')
    im_shape = img.shape
    im_scale_x = float(target_size) / float(im_shape[1])
    im_scale_y = float(target_size) / float(im_shape[0])
    img = cv2.resize(img, None, None, fx=im_scale_x, fy=im_scale_y)
    return img

def normalize(img, mean, std):
    img = img / 255.0
    mean = np.array(mean)[np.newaxis, np.newaxis, :]
    std = np.array(std)[np.newaxis, np.newaxis, :]
    img -= mean
    img /= std
    return img

def preprocess(img, img_size):
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    img = resize(img, img_size)
    img = img[:, :, ::-1].astype('float32')  # bgr -> rgb
    img = normalize(img, mean, std)
    img = img.transpose((2, 0, 1))  # hwc -> chw
    return img[np.newaxis, :]

def predict_config(model_file, params_file):
    '''
    函数功能：初始化预测模型predictor
    函数输入：模型结构文件，模型参数文件
    函数输出：预测器predictor
    '''
    # 根据预测部署的实际情况，设置Config
    config = Config()
    # 读取模型文件
    config.set_prog_file(model_file)
    config.set_params_file(params_file)
    # Config默认是使用CPU预测，若要使用GPU预测，需要手动开启，设置运行的GPU卡号和分配的初始显存。
    config.enable_use_gpu(3000, 0)
    # 可以设置开启IR优化、开启内存优化。
    config.switch_ir_optim()
    config.enable_memory_optim()
    config.enable_tensorrt_engine(workspace_size=1 << 30, precision_mode=PrecisionType.Float32,max_batch_size=1, min_subgraph_size=5, use_static=True, use_calib_mode=False)
    predictor = create_predictor(config)
    return predictor

def predict(predictor, img):

    '''
    函数功能：初始化预测模型predictor
    函数输入：模型结构文件，模型参数文件
    函数输出：预测器predictor
    '''
    input_names = predictor.get_input_names()
    for i, name in enumerate(input_names):
        input_tensor = predictor.get_input_handle(name)
        input_tensor.reshape(img[i].shape)
        input_tensor.copy_from_cpu(img[i].copy())
    # 执行Predictor
    predictor.run()
    # 获取输出
    results = []
    # 获取输出
    output_names = predictor.get_output_names()
    for i, name in enumerate(output_names):
        output_tensor = predictor.get_output_handle(name)
        output_data = output_tensor.copy_to_cpu()
        results.append(output_data)
    return results
# 创建一个字典来存储每个目标的主色彩
main_colors = {}
# 创建一个计数器用于切换颜色提取方法
counter = 0

def draw_bbox_image_mix(frame, result, label_list, threshold=0.5):

    def get_main_color_mean(bbox_image):
        main_color = np.mean(bbox_image, axis=(0, 1))
        return main_color

    def get_main_color_kmeans(bbox_image):
        
        reshaped_image = bbox_image.reshape(-1, 3)
        kmeans = KMeans(n_clusters=3)
        kmeans.fit(reshaped_image)
        main_color = kmeans.cluster_centers_[kmeans.labels_[0]]
        return main_color

    def get_dominant_color(image_bgr):
        # 增加图像的亮度，增加量减少到25
        image_brighter = np.clip(image_bgr + 20, 0, 255).astype(np.uint8)

        # Convert the image to HSV color space
        image_hsv = cv2.cvtColor(image_brighter, cv2.COLOR_BGR2HSV)

        # Define color ranges for red, yellow, blue, green
        colors = {"red": ([0, 100, 100], [10, 255, 255]), 
                "yellow": ([15, 100, 100], [45, 255, 255]),
                "green": ([55, 100, 100], [95, 255, 255]),
                "blue": ([105, 100, 100], [140, 255, 255])}

        # Calculate the number of pixels in each color range
        max_count = 0
        dominant_color = None
        for color, (lower, upper) in colors.items():
            lower = np.array(lower, dtype="uint8")
            upper = np.array(upper, dtype="uint8")
            mask = cv2.inRange(image_hsv, lower, upper)
            count = cv2.countNonZero(mask)
            if count > max_count:
                max_count = count
                dominant_color = color

        # Define BGR colors for red, yellow, blue, green
        bgr_colors = {"red": [0, 0, 255], 
                    "yellow": [0, 255, 255],
                    "green": [0, 255, 0], 
                    "blue": [255, 0, 0]}
        
        return bgr_colors[dominant_color]


    global main_colors
    global counter

    for res in result:
        cat_id, score, bbox = res[0], res[1], res[2:]
        if score < threshold:
            continue

        xmin, ymin, xmax, ymax = bbox
        xmin, ymin, xmax, ymax = map(int, [xmin, ymin, xmax, ymax])

        try:
            bbox_image = frame[ymin:ymax, xmin:xmax,:]
            # 查找主色彩，如果没有找到或者计数器达到特定值，则重新计算
            main_color = get_dominant_color(bbox_image)
            main_color = [int(bgr/2) for bgr in main_color]
            main_color = [str(int(bgr)) for bgr in main_color]

            main_color_str = "_".join(main_color)
            main_color = tuple([int(bgr) for bgr in main_color])
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), main_color, 2)

            label_id = label_list[int(cat_id)]
            cv2.putText(frame, label_id, (int(xmin), int(ymin-2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
            cv2.putText(frame, str(round(score,2)), (int(xmin-35), int(ymin-2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
            cv2.putText(frame, main_color_str, (int(xmin+25), int(ymin-2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, main_color, 2)
            return main_color_str+'\n'
        except Exception as e:
            print(e)
            pass

def initialize_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Camera not found!")
        return None
    return cap


    # 打开串口设备
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=0.5)

# 检查串口是否打
while not ser.isOpen():
    print(ser.name + ' cheking open status...')
    # print('Failed to open serial port. Please check the device path and permissions.')
    # sys.exit()

model_dir="pyyoloe/inference_model/ppyoloe_plus_crn_t_auxhead_320_300e_coco"
# 从infer_cfg.yml中读出label
infer_cfg = open(f"{model_dir}/infer_cfg.yml")
data = infer_cfg.read()
if yaml.__version__ >= '5.1':
    yaml_reader = yaml.load(data, Loader=yaml.FullLoader)
else:
    yaml_reader = yaml.load(data)
label_list = yaml_reader['label_list']
print(label_list)

# 配置模型参数
model_file = f"{model_dir}/model.pdmodel"
params_file = f"{model_dir}/model.pdiparams"
# 初始化预测模型
predictor = predict_config(model_file, params_file)

cv2.namedWindow("frame", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("frame", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# cap = cv2.VideoCapture(0)
cap = cv2.VideoCapture()
cap.open(0)

# 图像尺寸相关参数初始化
ret, img = cap.read()
im_size = 320 #不同的模型要选用不同的im_size：320和640
scale_factor = np.array([im_size * 1. / img.shape[0], im_size * 1. / img.shape[1]]).reshape((1, 2)).astype(np.float32)
im_shape = np.array([im_size, im_size]).reshape((1, 2)).astype(np.float32)
main_color_str="255_255_255\n"

is_human = True

cap = initialize_camera()

while True:

    if cap is None:
            cap = initialize_camera()
            time.sleep(1)  # 等待1秒再次尝试
            continue

    ret, frame = cap.read()
    if not ret:
        print("Error: Camera read failed!")
        cap.release()
        cap = None
        continue

    # print(frame)
    # 预处理
    data = preprocess(frame, im_size)

    time_start = time.time()
    if(ser.in_waiting > 0):
        human_status = ser.readline().decode().strip()
        print('human status:' + human_status)
        is_human = False if 'False' in human_status else True
    
    # 预测
    if is_human:
        result = predict(predictor, [data, scale_factor])
        # print(result)
        print('Time Cost：{}'.format(time.time()-time_start) , "s")

        cur_color=draw_bbox_image_mix(frame, result[0], label_list, threshold=0.4)
        if  cur_color:
            main_color_str=cur_color

        print(counter)
        counter+=1
        command = main_color_str
        if counter%10==0:
            # 向串口发送命令
            print("send:",command)
            ser.write(command.encode())
            print(ser.readline())


    cv2.imshow("frame", frame)
    key = cv2.waitKey(1)
    if key == 27:  # 27 is the ASCII value for the ESC key
        break
