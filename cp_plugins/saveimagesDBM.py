'''<b>SaveImagesDBM</b> - an example image processing module
'''
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.settings as cps
import os
import tempfile
import imagej.imageprocessor as ijiproc
import cellprofiler.measurements as cpmeas
from cellprofiler.modules.loadimages import C_FILE_NAME, C_PATH_NAME#constant value for file and path group
from suds.client import Client as wsclient#web service client

usr='kyan'
pwd='19821230'
host='babybear'
port=22;
remoteroot="test_seq/upload";

C_GROUP_TAG_SITE = "Metadata_Site"
C_GROUP_TAG_WELL = "Metadata_Well"
C_GROUP_TAG_PLATE = "Metadata_Plate"
C_GROUP_TAG_EXP = "Metadata_Experiment"
C_GROUP_TAG_PROJECT = "Metadata_Project"

class SaveImagesDBM(cpm.CPModule):
   
    module_name = "SaveImagesDBM"
    category = "ImageDB"
    variable_revision_number = 1
       
    def create_settings(self):
        self.saveimglist = []
        self.add_image(False)
        self.pathname_count = cps.HiddenCount(self.saveimglist)
        self.add_button = cps.DoSomething("add image set", "Add", self.add_image)
        
        self.input_cache_path = cps.DirectoryPath("cache location")
    
    def add_image(self, can_remove=True):
        group = cps.SettingsGroup()
        group.append("image_name",cps.ImageNameSubscriber("input image name:",doc = "image to save"))
        group.can_remove = can_remove
        if can_remove:
            group.append("remover", cps.RemoveSettingButton("Remove image output", "Remove", self.saveimglist, group))
        self.saveimglist.append(group)
        
    def settings(self):
        result=[self.pathname_count]
        result+=[group.image_name for group in self.saveimglist]
        result+=[self.input_cache_path]
        return result
    
    def visible_settings(self):
        result = []
        for group in self.saveimglist:
            result += [group.image_name]
            if group.can_remove:
                result += [group.remover]
        result += [self.add_button]
        result += [self.input_cache_path]       
        
        return result

    def run(self, workspace):
        import javabridge.jutil as jb

        measurements = workspace.measurements
        #pathname = measurements.get_measurement(cpmeas.IMAGE, pathname_feature)
        #filename = measurements.get_measurement(cpmeas.IMAGE, filename_feature)
        for group in self.saveimglist:
            filename_feature = C_FILE_NAME + "_" + group.image_name.value
            pathname_feature = C_PATH_NAME + "_" + group.image_name.value
            jb.attach()#initialize JVM
            input_image_name = group.image_name.value
            image_set = workspace.image_set
            assert isinstance(image_set, cpi.ImageSet)
            #prepare input image        
            input_image = image_set.get_image(input_image_name)        
            input_pixels = input_image.pixel_data
            ij_processor = ijiproc.make_image_processor((input_pixels*255.0).astype('float32'))
            
            cachepath=self.input_cache_path.get_absolute_path();
            if not os.path.exists(cachepath):
                os.makedirs(cachepath)

            tppath = tempfile.mktemp(prefix="img_",suffix= ".tif", dir=None)
            tppathname, tpfilename = os.path.split(tppath)
            print tpfilename
            localpath = os.path.join(cachepath, tpfilename)
            print localpath
            remotepath = remoteroot+"/"+tpfilename
            print remotepath
            #JavaScript API
            script = """
            importPackage(Packages.ij);
            strclasspath=java.lang.System.getProperty("java.class.path");
            var conn=new Packages.SFTP.SFTPConn(usr,pwd,host,port);
            Packages.ij.IJ.saveAs(new ImagePlus("",ij_processor),"TIFF", localpath);
            conn.put(remotepath,localpath);
            """
            #img.show();
            #Packages.ij.WindowManager.setCurrentWindow(img.getWindow());
            #"""
            in_params={"name":input_image_name,
                       "ij_processor": ij_processor,
                       "remotepath":remotepath,
                       "localpath":localpath,
                       "usr":usr,
                       "pwd":pwd,
                       "host":host,
                       "port":port}
            jb.run_script(script, bindings_in = in_params)
            
            #prepare output image
            #output_pixels = ijiproc.get_image(out_params["output_proc"], False)
                    
            if workspace.frame is not None:
                self.input_pixels = input_pixels
            #clean up ImageJ
            jb.run_script('Packages.ij.IJ.run("Close All");')
            jb.detach()#close JVM            
            
        grpnumber = measurements.get_measurement(cpmeas.IMAGE, cpmeas.GROUP_NUMBER)        
        grpindex = measurements.get_measurement(cpmeas.IMAGE, cpmeas.GROUP_INDEX)
        metaproject = measurements.get_measurement(cpmeas.IMAGE, C_GROUP_TAG_PROJECT)
        metaexp = measurements.get_measurement(cpmeas.IMAGE, C_GROUP_TAG_EXP)
        metaplate = measurements.get_measurement(cpmeas.IMAGE, C_GROUP_TAG_PLATE)
        metawell = measurements.get_measurement(cpmeas.IMAGE, C_GROUP_TAG_WELL)
        metasite = measurements.get_measurement(cpmeas.IMAGE, C_GROUP_TAG_SITE)
        
        print filename_feature,pathname_feature,grpnumber,grpindex,metaproject,metaexp,metaplate,metawell,metasite
        

        


    def prepare_settings(self, setting_values):
        npaths = int(setting_values[0])#get path count from hidden counter, the zero indicate the index of hidden counter in all setting, see setting(self)
        #print npaths
        del self.saveimglist[1:]
        for _ in range(1, npaths):
            self.add_image()

    def is_interactive(self):
        return False
