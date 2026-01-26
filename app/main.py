from controler.OpenCCCA import OpenCCCA
from argparse import ArgumentParser

if __name__=="__main__":
    
    parser = ArgumentParser("OpenCCCA")
    parser.add_argument("-of","--output_folder",required=False)
    parser.add_argument("-i","--input_file",required=False)
    parser.add_argument("-y","--year",required=False)
    args = parser.parse_args()
    
    output_folder=None
    input_file=None
    year = args.year 
    input_file = args.input_file 
    output_folder = args.output_folder 
        
    openccca = OpenCCCA()
    openccca.export_json(output_folder,year,input_file)
    