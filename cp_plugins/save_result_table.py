'''<b>Save_Result_Table</b> - an example image processing module
'''
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.settings as cps

import imagej.imageprocessor as ijiproc
from cellprofiler.modules.loadimages import C_FILE_NAME, C_PATH_NAME#constant value for file and path group
import cellprofiler.measurements as cpmeas

class Save_Result_Table(cpm.CPModule):
   
    module_name = "Save_Result_Table"
    category = "DImage_Meas"
    variable_revision_number = 1
       
    def create_settings(self):        
        self.input_image_name = cps.ImageNameSubscriber("Input image name:",doc = "Gray-value image only, no color image")
        self.output_directory = cps.DirectoryPath("output location",doc="");
        
    def settings(self):
        return [self.input_image_name, self.output_directory]
    
    def visible_settings(self):
        return [self.input_image_name, self.output_directory]

    def run(self, workspace):
        
        
        measurements = workspace.measurements
        import cellprofiler.utilities.jutil as jb
        jb.attach()#initialize JVM

        input_image_name = self.input_image_name.value
        filename_feature = C_FILE_NAME + "_" + input_image_name 
        filename = measurements.get_measurement(cpmeas.IMAGE, filename_feature)
        
        outputdir=self.output_directory.get_absolute_path();

        image_set = workspace.image_set

        #prepare input image        
        input_image = image_set.get_image(input_image_name, must_be_grayscale = True)
                
        input_pixels = input_image.pixel_data
        ij_processor = ijiproc.make_image_processor((input_pixels*255.0).astype('float32'))
        
        #JavaScript API
        script = """
        Packages.ij.IJ.saveAs("Results", outputdir+"/"+outputfname+".csv");
        """
        #img.show();
        #Packages.ij.WindowManager.setCurrentWindow(img.getWindow());
        #"""
        in_params={
                   "ij_processor": ij_processor,
                   "outputdir": outputdir,
                   "outputfname": filename}
        out_params={"output_proc":None}
        jb.run_script(script, bindings_in = in_params,bindings_out = out_params)
                
        
        workspace.input_pixels = input_pixels


    def is_interactive(self):
        return False
    #
    # display lets you use matplotlib to display your results. 
    #
    def display(self, workspace, figure):
        #prepare plot area
        figure.set_subplots((1,1))
        
        #display original image
        figure.subplot_imshow_grayscale(0, 0, workspace.input_pixels, title = self.input_image_name.value)
            