import numpy as np 
import cv2
import os 
import glob

from moviepy.editor import VideoFileClip, concatenate #moviepy kütüphanesini ekledik.

from tkinter import filedialog  #tkinter kütüphanesinde filedialog ile dosya seçtirme yapıyoruz.
from tkinter import *
from tkinter.ttk import *


ALLOWED_EXTENSIONS = set([ 'mkv', 'avi', 'mp4'])

anapencere = Tk()
anapencere.geometry("400x150")
anapencere.configure(bg="#215f66")

style= Style()
style.configure('TButton', font = ('calibri', 15,'bold'), borderwith= '2' , foreground = 'blue' , highlightcolor = 'black')

style.map('TButton', foreground = [('active', '!disabled', 'green')], background = [('active','!disabled','red')])

def UploadAction(event=None):
    anapencere.filename2 =  filedialog.askopenfilename(initialdir = "/", title = "Maç Videosunu Seçin",
                                             filetypes = (("mp4 files","*.mp4"),("all files","*.*")))
    print('Seçildi:', anapencere.filename2)
def UploadAction2(event=None):
    anapencere.filename =  filedialog.asksaveasfilename(initialdir = "/",title = "Yer Seçin",
                                              filetypes = (("mp4 files","*.mp4"),("all files","*.*")))  #dosya nereye yazılacak.
    print('Seçildi:', anapencere.filename)

yazi=Label(anapencere)

anapencere.title('OTOMATİK VİDEO ÖZETLEME')
Label(anapencere, text="Dosya seçin").grid(row=0,column=0,sticky='e')
Entry(anapencere).grid(row=0, column=1, padx=2, pady=2, sticky='we', columnspan=9)
Label(anapencere, text="Özet yeri").grid(row=1,column=0,sticky='e')
Entry(anapencere).grid(row=1, column=1, padx=2, pady=2, sticky='we', columnspan=9)
Checkbutton(anapencere, text="Görüntü İşlemeyi Dahil Et.").grid(row=2, column=1, columnspan=4, sticky='w')
Button(anapencere, text="Dosya Seç",command=UploadAction).grid(row=0,column=10,sticky='e'+'w', padx=2,pady=2)
Button(anapencere, text="Özet Yeri",command=UploadAction2).grid(row=1,column=10,sticky='e'+'w', padx=2)
Button(anapencere, text="Onayla",command=anapencere.quit).grid(row=2,column=10,sticky='e'+'w', padx=2)
anapencere.mainloop() #butona basılıncaya kadar ekranda kalması için.

anapencere.destroy() #dosya seçtirme işleminden sonra ekranın kapanması ve sonsuza kadar açık kalmaması için destroy kullandık.

clip = VideoFileClip(anapencere.filename2) #seçilen dosyayı işleme alıyoruz.

#video okuma
videokayit = cv2.VideoCapture(anapencere.filename2) #seçilen videoyu işleme alıyoruz.
success,image = videokayit.read()
count = 0
success = True
idx = 0

def cut(i):
  return(clip.audio.subclip(i,i+1).to_soundarray(fps=18000))   

def volume(array):
  return(np.sqrt(((1.0*array)**2).mean()))

volumes = [volume(cut(i)) for i in range(0,int(clip.duration-1))]

zero_secs = [i for i, v in enumerate(volumes) if v == 0.0]

ortalama_volume = np.array([sum(volumes[i:i+10])/10
                             for i in range(len(volumes)-10)])

azalma = np.diff(ortalama_volume)[1:]<=0
artis = np.diff(ortalama_volume)[:-1]>=0

time = (artis * azalma).nonzero()[0]
vol = ortalama_volume[time]


time = time[vol>np.percentile(vol,80)] #volume değerinin yüzde kaçını alacağını bu değerle belirliyoruz. Kullanıcının girdiği değer.
finaltime=[time[0]]  


for zaman in time:
    if (zaman - finaltime[-1]) < 60:
        if ortalama_volume[zaman] > ortalama_volume[finaltime[-1]]:
            finaltime[-1] = zaman
    else:
        finaltime.append(zaman)
        final = concatenate([clip.subclip(max(zaman-10,0),min(zaman+8, clip.duration)) #keseceği anın eksi ve artı ne kadar saniye alacak belirleniyor.
                     for zaman in finaltime])
  

while success:
	#image'i hsv renk uzayına çevirdik
	hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
	#beyaz
	lower_beyaz = np.array([0,0,0])
	upper_beyaz = np.array([0,0,255])
	
	#yesil
	lower_yesil = np.array([40,40, 40])
	upper_yesil = np.array([70, 255, 255])
	
	#kirmizi
	lower_kirmizi = np.array([0,100,255])
	upper_kirmizi = np.array([146,255,255])
	
	#mavi
	lower_mavi = np.array([110,50,50])
	upper_mavi = np.array([130,255,255])
	
	#kaleci
	lower_kaleci = np.array([70,120,120])
	upper_kaleci = np.array([70,205,185])
	
    #sahanın yeşilini ayırıp diğer yerleri net bir şekilde işaretlemek için maskeye upper ve lower yesil değerleri verdik
	mask = cv2.inRange(hsv, lower_yesil, upper_yesil)
    #maske
	res = cv2.bitwise_and(image, image, mask=mask)
	
	#hsv renk uzayından graye çevirdik.
	
	res_bgr = cv2.cvtColor(res,cv2.COLOR_HSV2BGR)
	res_gray = cv2.cvtColor(res,cv2.COLOR_BGR2GRAY)

        #morfolojik işlem operatörleri kullanırız.Oyuncuları daha iyi tespit edebilmek için Closing(Kapanım) operatörü kullanılmıştır.
	kernel = np.ones((13,13),np.uint8)
	thresh = cv2.threshold(res_gray,127,255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
	thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
	
    #find contours in threshold image     
	contours,hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
	
	prev = 0
	font = cv2.FONT_HERSHEY_SIMPLEX
	
	for c in contours:
		x,y,w,h = cv2.boundingRect(c)
		
		#oyuncu tespiti
		if(h>=(1.7)*w):
			if(w>30 and h>= 30):  #okunan karede yükseklik ve genişlik durumuna göre bakıyoruz.
				idx = idx+1
				player_img = image[y:y+h,x:x+w]
				player_hsv = cv2.cvtColor(player_img,cv2.COLOR_BGR2HSV)
				mask3 = cv2.inRange(player_hsv, lower_kaleci, upper_kaleci)
				res3 = cv2.bitwise_and(player_img, player_img, mask=mask3)
				res3 = cv2.cvtColor(res3,cv2.COLOR_HSV2BGR)
				res3 = cv2.cvtColor(res3,cv2.COLOR_BGR2GRAY)
				yesil = cv2.countNonZero(res3)	
				if(yesil>=20):
				       
					#kalecinin tespiti ve kutu ayarlaması.
					cv2.putText(image, 'Kaleci', (x-2, y-2), font, 0.8, (0,255,0), 2, cv2.LINE_AA)
					cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),3)
				else:
					pass
					
			if(w>10 and h>= 10):
				idx = idx+1
				player_img = image[y:y+h,x:x+w]
				player_hsv = cv2.cvtColor(player_img,cv2.COLOR_BGR2HSV)
				mask3 = cv2.inRange(player_hsv, lower_kaleci, upper_kaleci)
				res3 = cv2.bitwise_and(player_img, player_img, mask=mask3)
				res3 = cv2.cvtColor(res3,cv2.COLOR_HSV2BGR)
				res3 = cv2.cvtColor(res3,cv2.COLOR_BGR2GRAY)
				yesil = cv2.countNonZero(res3)
			
				mask1 = cv2.inRange(player_hsv, lower_mavi, upper_mavi)
				res1 = cv2.bitwise_and(player_img, player_img, mask=mask1)
				res1 = cv2.cvtColor(res1,cv2.COLOR_HSV2BGR)
				res1 = cv2.cvtColor(res1,cv2.COLOR_BGR2GRAY)
				mavi = cv2.countNonZero(res1)
				
				mask2 = cv2.inRange(player_hsv, lower_kirmizi, upper_kirmizi)
				res2 = cv2.bitwise_and(player_img, player_img, mask=mask2)
				res2 = cv2.cvtColor(res2,cv2.COLOR_HSV2BGR)
				res2 = cv2.cvtColor(res2,cv2.COLOR_BGR2GRAY)
				kirmizi = cv2.countNonZero(res2)

				if(mavi >= 25):
					#1.takımın takımının tespiti ve işaretlendiğinde üstünde çıkacak kutunun ayarları
					cv2.putText(image, 'team1', (x-2, y-2), font, 0.6, (255,0,0), 2, cv2.LINE_AA)
					cv2.rectangle(image,(x,y),(x+w,y+h),(255,0,0),3)
				else:
					pass
				if(kirmizi>=25):
					#2.takımın takımının tespiti ve işaretlendiğinde üstünde çıkacak kutunun ayarları
					cv2.putText(image, 'team2', (x-2, y-2), font, 0.6, (0,0,255), 2, cv2.LINE_AA)
					cv2.rectangle(image,(x,y),(x+w,y+h),(0,0,255),3)
				else:
					pass
			
		if((h>=5 and w>=5) and (h<=30 and w<=30)):
			player_img = image[y:y+h,x:x+w]
		
			player_hsv = cv2.cvtColor(player_img,cv2.COLOR_BGR2HSV)
            
	cv2.imwrite("./Cropped/frame%d.jpg" % count, res)
	image=cv2.resize(image, (640,480))
	count += 1
	cv2.imshow('Match Detection',image)
	if cv2.waitKey(1) & 0xFF == ord('q'): #program q ile sonlandırıyoruz.
		break
	success,image = videokayit.read() 
final.to_videofile(anapencere.filename)  #yazacağı mp4 video dosyası. anapencere.filename ile kullanıcının nereye yazacağına göre burada işleme alıyoruz.
   
videokayit.release()
cv2.destroyAllWindows()
