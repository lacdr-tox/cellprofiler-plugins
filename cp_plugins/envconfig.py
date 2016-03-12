
'''envconfig.py - a plugin that loads some files

'''
import os
import sys

from bioformats import load_using_bioformats
import cellprofiler.settings as cps
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.measurements as cpmeas
from cellprofiler.modules.loadimages import C_FILE_NAME, C_PATH_NAME
import cellprofiler.utilities.jutil as jb
import imagej.windowmanager as ijwm
import imagej.imageprocessor as ijiproc

class envconfig(cpm.CPModule):
    variable_revision_number=1
    module_name = "envconfig"
    category = "File Processing"
    sys.path.append(r"E:\Program Files\CellProfilerTrunk20130401200712\site-packages\lib\share")
    sys.path.append(r"E:\Program Files\CellProfilerTrunk20130401200712\site-packages\lib\python\py4j")
    sys.path.append(r"E:\Program Files\CellProfilerTrunk20130401200712\site-packages\lib\python")
    print sys.path
            
    def create_settings(self):
        self.image_name = cps.ImageNameProvider("Image name", "DNA")
        self.output_image_name = cps.ImageNameProvider("Output image name:",
            # The second parameter holds a suggested name for the image.
            "OutputImage",
            doc = """This is the image resulting from the operation.""")
        self.pathnames = []
        self.add_pathname(False)
        self.pathname_count = cps.HiddenCount(self.pathnames)
        self.add_button = cps.DoSomething("Add another file", "Add",
                                          self.add_pathname)


        
    def add_pathname(self, can_remove=True):
        group = cps.SettingsGroup()
        group.append("path", cps.Text(
            "Path to file", r"e:\test.tif"))
        group.can_remove = can_remove
        if can_remove:
            group.append(
                "remover", 
                cps.RemoveSettingButton(
                    "Remove this path", "Remove", self.pathnames, group))
        self.pathnames.append(group)
        
    def settings(self):
        return [self.pathname_count, self.image_name, self.output_image_name] + \
               [group.path for group in self.pathnames]
    
    def visible_settings(self):
        result = [self.image_name, self.output_image_name]
        for group in self.pathnames:
            result += [group.path]
            if group.can_remove:
                result += [group.remover]
        result += [self.add_button]
        return result
    
    def prepare_run(self, workspace):
        measurements = workspace.measurements
        filename_feature = C_FILE_NAME + "_" + self.image_name.value
        pathname_feature = C_PATH_NAME + "_" + self.image_name.value
        for i, group in enumerate(self.pathnames):
            image_number = i+1
            pathname, filename = os.path.split(group.path.value)
            print pathname, filename
            measurements.add_measurement(
                cpmeas.IMAGE, pathname_feature, pathname,
                image_set_number = image_number)
            measurements.add_measurement(
                cpmeas.IMAGE, filename_feature, filename,
                image_set_number = image_number)
        return True
    
    def run(self, workspace):
        measurements = workspace.measurements
        imgname = self.image_name.value
        filename_feature = C_FILE_NAME + "_" + imgname
        pathname_feature = C_PATH_NAME + "_" + imgname
        pathname = measurements.get_measurement(
            cpmeas.IMAGE, pathname_feature)
        filename = measurements.get_measurement(
            cpmeas.IMAGE, filename_feature)
        path = os.path.join(pathname, filename)
        data = load_using_bioformats(path)
        
        image = cpi.Image(data)
        workspace.image_set.add(self.image_name.value, image)
        
        ij_processor = ijiproc.make_image_processor((image.pixel_data * 255.0).astype('float32'))
        gsize=2
        rsize=256
        jb.attach()
        script = """       
        var img=Packages.ij.ImagePlus(name,ij_processor);
        Packages.ij.IJ.run(img, "8-bit", "");
        Packages.ij.IJ.run(img, "WMC Segment", "g_size="+gsize+" r_size="+rsize+" noise=10 low_seed=10 high_seed=50 low_bound=0.60 high_bound=0.80 min_std=0.20 is_equalize use_paraboloid");
        img.show();
        Packages.ij.WindowManager.setCurrentWindow(img.getWindow());
        """
        r = jb.run_script(script, bindings_in = {"name":imgname,"ij_processor": ij_processor,"gsize":gsize,"rsize":rsize})
        
        image_plus = ijwm.get_current_image()
        ij_processor = image_plus.getProcessor()
        pixels = ijiproc.get_image(ij_processor).astype('float32') / 255.0
        
        
        
        output_image_name=self.output_image_name.value
        output_image = cpi.Image(pixels, parent_image = image)
        workspace.image_set.add(output_image_name, output_image)
        jb.detach()

    def prepare_settings(self, setting_values):
        npaths = int(setting_values[0])
        del self.pathnames[1:]
        for _ in range(1, npaths):
            self.add_pathname()

    def is_load_module(self):
        return True