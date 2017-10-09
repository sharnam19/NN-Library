# from layers.util.layer import *
# from layers.util.util import *
# from layers.util.activations import *
# from layers.util.normalization import *
# from layers.util.convolution import *
# from layers.util.loss import *
from layers.layer import *
from operator import mul
import matplotlib.pyplot as plt
import pickle
import json
class NN:
    
    def __init__(self,input_shape,update_params,initialization="normal"):
        self.J=[]
        self.layers=[]
        self.accuracies=[]
        self.out_shape=[input_shape]
        self.update_params=update_params
        self.initialization = initialization
        
    def initializer(self,mean=0,shift=0.01,shape=None,initialization="normal"):
        if initialization == "normal":
            init = shift*np.random.standard_normal(shape)+mean
        elif initialization == "xavier":
            init = np.random.standard_normal(shape)/(shape[0]**0.5)
        elif initialization == "xavier2":
            if len(shape)==2:
                init = np.random.standard_normal(shape)/((shape[0]/2.)**0.5)
            elif len(shape)==4:
                init = np.random.standard_normal(shape)/((reduce(mul,shape[1:],1)/2.)**0.5)
        return init

    def add(self,layer_name,affine_out=None,
            padding_h=None,padding_w=None,
            pooling_params=None,
            num_kernels=None,kernel_h=None,kernel_w=None,convolution_params=None,
            batch_params=None,
            output=None,
            mean=0,shift=0.01):
        
        outshape = len(self.out_shape[-1])
        
        if layer_name == "affine" and outshape==2:
            
            N,D = self.out_shape[-1]
            W = self.initializer(mean,shift,(D,affine_out),initialization=self.initialization)
            b = np.zeros(affine_out,)
            self.layers.append(Affine(W,b,self.update_params))
            self.out_shape.append((N,affine_out))
            
        elif layer_name == "flatten" and outshape>2:
        
            self.layers.append(Flatten())
            shape = self.out_shape[-1]
            self.out_shape.append((shape[0],reduce(mul,shape[1:],1)))
        
        elif layer_name == "relu":
            
            self.layers.append(Relu())
            shape = self.out_shape[-1]
            self.out_shape.append(shape)
        
        elif layer_name == "sigmoid":
            
            self.layers.append(Sigmoid())
            shape = self.out_shape[-1]
            self.out_shape.append(shape)
            
        elif layer_name == "tanh":
            
            self.layers.append(Tanh())
            shape = self.out_shape[-1]
            self.out_shape.append(shape)
            
        elif layer_name == "leaky_relu":
            
            self.layers.append(LeakyRelu())
            shape = self.out_shape[-1]
            self.out_shape.append(shape)
            
        elif layer_name == "padding" and outshape == 4:
            
            shape = self.out_shape[-1]
            self.layers.append(Padding(padding_h,padding_w))
            self.out_shape.append((shape[0],shape[1],2*padding_h+shape[2],2*padding_w+shape[3]))
            
        elif layer_name == "pooling" and outshape == 4:
            
            self.layers.append(Pooling(pooling_params))
            
            Ph = pooling_params.get('pooling_height',2)
            Pw = pooling_params.get('pooling_width',2)
            PSH = pooling_params.get('pooling_stride_height',2)
            PSW = pooling_params.get('pooling_stride_width',2)
    
            N,C,H,W = self.out_shape[-1]
            Hout = (H-Ph)//PSH + 1
            Wout = (W-Pw)//PSW + 1
            
            self.out_shape.append((N,C,Hout,Wout))
    
        elif layer_name == "convolution" and outshape == 4:
            
            N,C,H,W = self.out_shape[-1]
            S = convolution_params.get('stride',1)
            Hout = abs(H-kernel_h)//S + 1
            Wout = abs(W-kernel_w)//S + 1
        
            W = self.initializer(mean,shift,(num_kernels,C,kernel_h,kernel_w),initialization=self.initialization)
            b = np.zeros((num_kernels,))
            self.layers.append(Convolution(W,b,convolution_params,self.update_params))
            self.out_shape.append((N,num_kernels,Hout,Wout))
            
        elif layer_name == "softmax" and outshape==2:
            
            self.layers.append(Softmax())
            self.out_shape.append((1))
            
        elif layer_name == "svm" and outshape==2:
            
            self.layers.append(SVM())
            self.out_shape.append((1))
            
        elif layer_name == "batch_normalization" and outshape==2:
            
            shape = self.out_shape[-1]
            D = shape[1]
            
            gamma = np.ones((D,))
            beta = np.zeros((D,))
            self.layers.append(BatchNormalization(gamma,beta,batch_params,self.update_params))
            self.out_shape.append(shape)
        elif layer_name == "spatial_batch" and outshape==4:
            
            shape = self.out_shape[-1]
            gamma = np.ones((shape[1],))
            beta = np.zeros((shape[1],))
            self.layers.append(SpatialBatchNormalization(gamma,beta,batch_params,self.update_params))
            self.out_shape.append(shape)
        else:
            print "Check Shapes"
            raise NotImplementedError
    
    
    def train(self,X,y):
        self.test(X[:64],y[:64])
        print("Initial Cost :"+str(self.J[-1]))
        print("Initial Accuracy :"+str(self.accuracies[-1]))
        
        for i in range(self.update_params['epoch']):
            sample  = np.random.randint(0,X.shape[0],(self.out_shape[0][0],))
            inp = X[sample]
            loss = 0.0
            for layer in self.layers[:-1]:
                inp = layer.forward(inp)
                loss += layer.loss_reg()
            
            scores,inp = self.layers[-1].forward(inp,y[sample])
            
            for layer in self.layers[::-1]:
                inp = layer.backprop(inp)
            
            self.test(X[sample],y[sample])
            print("Cost at Iteration "+str(i)+" : "+str(self.J[-1]))
            print("Accuracy at Iteration "+str(i)+" : "+str(self.accuracies[-1]))
                  
    def test(self,X,y):
        loss = 0.0
        inp = X
        for layer in self.layers[:-1]:
            inp = layer.forward(inp)
            loss += layer.loss_reg()
        
        scores,inp = self.layers[-1].forward(inp,y)
        self.accuracies.append(self.accuracy(scores,y))
        self.J.append(inp+loss)
        
    def accuracy(self,scores,y):
        return 1.0*np.sum(np.argmax(scores,axis=1)==y)/y.shape[0]
    
    def predict(self,X):
        inp = X
        for layer in self.layers:
            inp = layer.forward(inp)
            
        return np.argmax(inp,axis=1)
    
    def save(self,filename):
        outfile = open('models/'+filename, 'wb')
        pickle.dump(self,outfile)
    
    @staticmethod
    def load(filename):
        infile = open('models/'+filename,'rb')
        return pickle.load(infile)
    
    def plot(self):
        plt.plot(self.J)
        plt.show()
        
if __name__== "__main__":
    model = NN(input_shape=(64,1,50,50),update_params={'alpha':1e-3,'method':'adam','epoch':100,'offset':1e-7,'reg':0.01,'reg_type':'L2'},initialization="xavier2")
    model.add("padding",padding_h=2,padding_w=2)
    model.add("convolution",num_kernels=64,kernel_h=3,kernel_w=3,convolution_params={"stride":1})
    model.add("pooling",pooling_params={"pooling_height":2,"pooling_stride_height":2,
                                        "pooling_stride_height":2,"pooling_stride_height":2})
    model.add("relu")
    model.add("convolution",num_kernels=128,kernel_h=3,kernel_w=3,convolution_params={"stride":1})
    model.add("pooling",pooling_params={"pooling_height":2,"pooling_stride_height":2,
                                        "pooling_stride_height":2,"pooling_stride_height":2})
    
    model.add("relu")
    model.add("flatten")
    model.add("affine",affine_out=128)
    model.add("affine",affine_out=64)
    model.add("affine",affine_out=16)
    model.add("affine",affine_out=5)
    model.add("softmax")
    
    data = json.load(open("data/data.json","rb"))
    trainX = np.array(data['trainX'])
    trainY = np.array(data['trainY'],dtype=np.int32)
    
    validX = np.array(data['validX'])
    validY = np.array(data['validY'],dtype=np.int32)
    
    testX = np.array(data['testX'])
    testY = np.array(data['testY'],dtype=np.int32)
    model.train(trainX,trainY)
    model.save("model1.pkl")
