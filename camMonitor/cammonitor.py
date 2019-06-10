import cv2
import subprocess as sp
import logging
import time


class CamMonitor():
    def __init__(self):
        self.rtmpUrl='rtmp://127.0.0.1:1935/live/stream'
        self.file_path='out.avi'
        self.camera=camera = cv2.VideoCapture(0)
        self.size = (int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self.fps=int(self.camera.get(cv2.CAP_PROP_FPS))
        sizeStr='{}x{}'.format( self.size[0],self.size[1])
        print('size:' +sizeStr  + ' fps:' + str(self.fps) + ' hz:')
        # 视频文件输出
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(self.file_path, self.fourcc, self.fps, self.size)
        # ffmpeg执行的命令，通过管道 共享数据的方式
        self.command=['ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-vcodec','rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', sizeStr,
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',
            '-f', 'flv',
            self.rtmpUrl]
        self.pushrtmpProcess = sp.Popen(self.command, stdin=sp.PIPE)  # ,shell=False
        self.open_switch=False
        # self.background_image=None
        self.former_frame=None
        self.motion_detect_on=False
    def run(self):
        self.open_switch = True
        # count = 0
        time.sleep(1)
        while self.open_switch:
            ###########################图片采集
            # count = count + 1
            ret, frame = self.camera.read()  # 逐帧采集视频流
            if self.former_frame is None:
                # 背景图，或者说第一帧的图片进行亮度减小，高斯模糊等处理，减少光照振动等因素的影响
                # 背景图的作用是与后面的图片进行对比
                logging.info('background image')
                self.former_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                self.former_frame = cv2.GaussianBlur(self.former_frame, (21, 21), 0)
                continue
            if not ret:
                break
            if self.motion_detect_on:
                frame=self.motion_detect(frame)
            # 结果帧处理 存入文件 / 推流 / ffmpeg 再处理
            self.pushrtmpProcess.stdin.write(frame)  # 存入管道用于直播
            # if self.pushrtmpProcess.poll():
            self.out.write(frame)  # 同时 存入视频文件 记录直播帧数据
            # if cv2.waitKey(25)& 0xFF == ord('q'):
            #     break
        print("Over!")
    def stop(self):
        self.open_switch=False
        # self.pushrtmpProcess.terminate()
        logging.debug('process terminated')

    def motion_detect(self,frame):
        # 读入帧
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 高斯平滑 模糊处理 减小光照 震动等原因产生的噪声影响
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)
        # 检测背景和帧的区别
        diff = cv2.absdiff(self.former_frame, gray_frame)
        # 将区别转为二值
        diff = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        # 定义结构元素
        # es = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 4))
        # 膨胀运算
        diff = cv2.dilate(diff, None, iterations=2)
        # 搜索轮廓
        cnts, hierarcchy = cv2.findContours(diff.copy(),
                                            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        """
        cv.findContours()
            参数：
                1 要寻找轮廓的图像 只能传入二值图像，不是灰度图像
                2 轮廓的检索模式，有四种：
                    cv2.RETR_EXTERNAL表示只检测外轮廓
                    cv2.RETR_LIST检测的轮廓不建立等级关系
                    cv2.RETR_CCOMP建立两个等级的轮廓，上面的一层为外边界，
                        里面的一层为内孔的边界信息。
                        如果内孔内还有一个连通物体，这个物体的边界也在顶层
                    cv2.RETR_TREE建立一个等级树结构的轮廓
                3 轮廓的近似办法
                    cv2.CHAIN_APPROX_NONE存储所有的轮廓点，
                        相邻的两个点的像素位置差不超过1，
                        即max（abs（x1-x2），abs（y2-y1））==1
                    cv2.CHAIN_APPROX_SIMPLE压缩水平方向，垂直方向，对角线方向的元素，
                        只保留该方向的终点坐标，例如一个矩形轮廓只需4个点来保存轮廓信息
            返回值:
                contours:一个列表，每一项都是一个轮廓， 不会存储轮廓所有的点，只存储能描述轮廓的点
                hierarchy:一个ndarray, 元素数量和轮廓数量一样， 
                    每个轮廓contours[i]对应4个hierarchy元素hierarchy[i][0] ~hierarchy[i][3]，
                    分别表示后一个轮廓、前一个轮廓、父轮廓、内嵌轮廓的索引编号，如果没有对应项，则该值为负数
        """
        for c in cnts:
            # 轮廓太小忽略 有可能是斑点噪声
            if cv2.contourArea(c) < 10000:
                continue
            # 将轮廓画出来
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # 记录这一帧作为下次的对比对象
        self.former_frame=gray_frame
        return frame
        # cv2.imshow("contours", frame)
        # cv2.imshow("diff", diff)

if __name__=='__main__':
    cam=CamMonitor()
    cam.run()