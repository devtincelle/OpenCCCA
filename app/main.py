from controler.OpenCCCA import OpenCCCA
from argparse import ArgumentParser

if __name__=="__main__":
    
    parser = ArgumentParser("OpenCCCA")
    parser.add_argument("-of","--output_folder",required=False)
    parser.add_argument("-i","--input_pdf",required=False)
    args = parser.parse_args()
    
    output_folder=None
    input_pdf=None
    
    if args.output_folder  :
        input_pdf = args.input_pdf 
    if  args.input_pdf :
        output_folder = args.output_folder 
        
    openccca = OpenCCCA()
    openccca.export_json(output_folder,input_pdf)
    