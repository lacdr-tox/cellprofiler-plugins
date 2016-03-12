'''<b>Cyto_NC_Segment</b> - performing cytoplasm segmentation using both nuclei and cytoplasm channel

<hr>
<p>
The segmentation algorithm first obtain a corase region of all cytoplasm using hysteresis thresholding.
The corase region is divided into individual region by using a seeded watershed using nuclei mask as seeds.
</p>


'''

import os
import sys

import cellprofiler.settings as cps
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm

import imagej.imageprocessor as ijiproc


class Cyto_NC_Segment(cpm.CPModule):
    module_name = "Cyto_NC_Segment"
    category = "DImage"
    variable_revision_number = 1
        
    def create_settings(self):
        self.input_nc_mask_image_name = cps.ImageNameSubscriber("nuclei mask image:",
                                                                doc = """
                                                                nucleus mask image,
                                                                white for foreground pixels,
                                                                black for background pixels
                                                                """)
        
        self.input_nc_gray_image_name = cps.ImageNameSubscriber("nuclei gray image",
                                                                doc = """
                                                                nucleus gray-value image, preferable 8-bit
                                                                """)
        
        self.input_cyto_gray_image_name = cps.ImageNameSubscriber("cytoplasm gray image",
                                                                  doc = """
                                                                  cytoplasm gray-value image, preferable 8-bit
                                                                  """)
        
        self.output_image_name = cps.ImageNameProvider("output image:","OutputImage", 
                                                       doc = """
                                                       binary mask of cytoplasm,
                                                       white for foreground pixels,
                                                       black for background pixels
                                                       """)
        
        self.input_gaussian_filter = cps.Float("Gaussian filter size",value=3,
                                               doc = """
                                               Gaussian filter size for noise suppression in cytoplasm channel,
                                               recommended around 6~8, suppressing pixel noises or texture                                               
                                               """)
        
        self.input_rolling_ball = cps.Float("rolling ball size",value=256,
                                            doc = """
                                            rolling ball kernel size, recommended around 1/4 of image dimensionality, remove uneven illumination
                                            """)
        
        self.input_noise = cps.Float("noise",value=5,
                                     doc = """
                                     noise-tolerant level, higher value means less cutting, lower value means more cutting
                                     """)
        
        self.input_low_seed = cps.Float("low seed",value=10,
                                        doc = """
                                        initial intensity value for background
                                        """)
        
        self.input_high_seed = cps.Float("high seed",value=50,
                                         doc = """
                                         initial intensity value for foreground
                                         """)
        
        self.input_dilate_dist = cps.Float("dilate distance",value=0, 
                                           doc = """
                                           expand the mask given pixel distance if necessary, the value is the dilation distance in pixel,
                                           otherwise the value is 0 for no dilation
                                           """)
        
    def settings(self):
        return [self.input_nc_mask_image_name,
                self.input_nc_gray_image_name,
                self.input_cyto_gray_image_name, 
                self.output_image_name, 
                self.input_gaussian_filter,
                self.input_rolling_ball,
                self.input_noise,
                self.input_low_seed,
                self.input_high_seed,
                self.input_dilate_dist]
    

    def visible_settings(self):
        result = [self.input_nc_mask_image_name,
                  self.input_nc_gray_image_name,
                  self.input_cyto_gray_image_name, 
                  self.output_image_name,
                  self.input_gaussian_filter,
                  self.input_rolling_ball,
                  self.input_noise,
                  self.input_low_seed,
                  self.input_high_seed,
                  self.input_dilate_dist]
        return result

    def run(self, workspace):
        import cellprofiler.utilities.jutil as jb
        jb.attach()#initialize JVM
        
        nc_mask_image_name = self.input_nc_mask_image_name.value
        nc_gray_image_name = self.input_nc_gray_image_name.value
        cyto_gray_image_name = self.input_cyto_gray_image_name.value        
        output_image_name = self.output_image_name.value
        workspace.gsize = self.input_gaussian_filter.value
        workspace.rsize = self.input_rolling_ball.value
        workspace.noise = self.input_noise.value
        workspace.lowseed = self.input_low_seed.value
        workspace.highseed = self.input_high_seed.value
        workspace.dilatedist = self.input_dilate_dist.value
        
        image_set = workspace.image_set
        
        #prepare input image        
        input_image_nc_mask = image_set.get_image(nc_mask_image_name, must_be_grayscale = True)
        input_image_nc_gray = image_set.get_image(nc_gray_image_name, must_be_grayscale = True)
        input_image_cyto_gray = image_set.get_image(cyto_gray_image_name, must_be_grayscale = True)
        
        input_pixels_nc_mask = input_image_nc_mask.pixel_data
        input_pixels_nc_gray = input_image_nc_gray.pixel_data
        input_pixels_cyto_gray = input_image_cyto_gray.pixel_data
        
        ij_processor_nc_mask = ijiproc.make_image_processor((input_pixels_nc_mask*255.0).astype('float32'))
        ij_processor_nc_gray = ijiproc.make_image_processor((input_pixels_nc_gray*255.0).astype('float32'))
        ij_processor_cyto_gray = ijiproc.make_image_processor((input_pixels_cyto_gray*255.0).astype('float32'))
        #JavaScript API
        script = """
	
	java.lang.System.out.println(java.lang.System.getProperty( "java.class.path" ));
	
        var ncmask = Packages.ij.ImagePlus("nc_mask",ij_processor_nc_mask);
        var ncgray = Packages.ij.ImagePlus("nc_gray",ij_processor_nc_gray);
        var cytogray = Packages.ij.ImagePlus("cyto_gray",ij_processor_cyto_gray);
        
        Packages.ij.IJ.run(ncmask, "8-bit", "");
        Packages.ij.IJ.run(ncgray, "8-bit", "");
        Packages.ij.IJ.run(cytogray, "8-bit", "");
        
        ncmaskIP=ncmask.getProcessor();
        ncgrayIP=ncgray.getProcessor();
        cytograyIP=cytogray.getProcessor();
        
        masker=new Packages.DImage.CP.CytoNCMask();
        masker.cytogsize=gsize;
        masker.cytorsize=rsize;
        masker.cytolowseed=lowseed;
        masker.cytohighseed=highseed;
        masker.cytonoise=noise;
        masker.cytodilate=dilatedist;
        masker.iscytoequalize=true;

	output_imgplus=masker.cpmasking(ncmask, ncgray, cytogray);
        output_proc=output_imgplus.getProcessor();
        """
        #img.show();
        #Packages.ij.WindowManager.setCurrentWindow(img.getWindow());
        #"""
        in_params={
                   "name":output_image_name,
                   "ij_processor_nc_mask": ij_processor_nc_mask,
                   "ij_processor_nc_gray": ij_processor_nc_gray,
                   "ij_processor_cyto_gray": ij_processor_cyto_gray,
                   "gsize":workspace.gsize,
                   "rsize":workspace.rsize,
                   "noise":workspace.noise,
                   "lowseed":workspace.lowseed,
                   "highseed":workspace.highseed,
                   "dilatedist":workspace.dilatedist}
        out_params={"output_proc":None}
        jb.run_script(script, bindings_in = in_params,bindings_out = out_params)
        #prepare output image
        output_pixels = ijiproc.get_image(out_params["output_proc"], False)
        output_image = cpi.Image(output_pixels, parent_image = input_image_cyto_gray)
        
        #write output
        image_set.add(output_image_name, output_image)
        
        workspace.intput_pixels_nc_gray = input_pixels_nc_gray
        workspace.intput_pixels_cyto_gray = input_pixels_cyto_gray
        workspace.output_pixels = output_pixels


    def is_interactive(self):
        return False
    
    def display(self, workspace, figure):
          #prepare plot area
        figure.set_subplots((3,1))
        
        #display original image
        figure.subplot_imshow_grayscale(0, 0, workspace.intput_pixels_nc_gray, title = self.input_nc_gray_image_name.value)
        
        figure.subplot_imshow_grayscale(1, 0, workspace.intput_pixels_cyto_gray, title = self.input_cyto_gray_image_name.value)
        
        #display binary mask
        figure.subplot_imshow_grayscale(2, 0, workspace.output_pixels, title = self.output_image_name.value)
