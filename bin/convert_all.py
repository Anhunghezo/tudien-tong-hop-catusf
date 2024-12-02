#!/usr/bin/env python3
''' Script to build all dictionaries with all formats
    Usage:
    ./bin/convert_all.py --input_folder=./ext-dict --output_folder=./ext-output --extension=tab
'''

import argparse
from fileinput import filename
import glob
import os.path
import os
import subprocess
from iso_language_codes import language_name
import shlex

def readDicInfo(filepath):
    ''' Read metadata of dictionary with the following format

            Name = Dictionary of xyz
            Description = Description of this dictionary
            Source = en
            Target = vi
            Inflections = "NoInflections.txt"
            Version = 1.1

        Target and Source are the ISO 2-character codes of the language.
        Name, Source and Target are mandatory fields.
    '''

    valuemap = {}

    try:
        file = open(filepath, encoding='utf-8')

        lines = file.readlines()

        for line in lines:
            line = line.strip()

            if not line:
                continue
         
            key, value = line.split('=')

            valuemap[key.strip()] = value.strip()

        valuemap['FullSource'] = language_name(valuemap['Source'])
        valuemap['FullTarget'] = language_name(valuemap['Target'])

        keys = ['Name', 'Source', 'Target'] # Mandatory keys

        for i, k in enumerate(keys):
            if not k in valuemap:
                print(f'Missing key: "{keys[i]}"')

                return None
            
    except IOError as err:
        print(err)
        return None

#    print(valuemap)

    return valuemap


def execute_shell(cmd_line, message="", printout=True):
    """
    Executes a shell command and handles any errors that occur during execution.

    Parameters:
    cmd_line (str): The command line string to be executed.
    message (str): An optional message to include in error output if the command fails.
    printout (bool): If True, prints the command line before execution.

    Returns:
    bool: True if the command executes successfully, False if an error occurs.
    """
    try:
        if printout:
            print(cmd_line)

        # subprocess.run(shlex.split(cmd_line), check=True)
        subprocess.call(cmd_line, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        if message:
            print(f"Error {message}: {e}")
        else:
            print(f"Error executing shell: {e}")

        return False
    
DEBUG_FLAG = False

import re

def escape_forbidden_chars(text, forbidden_chars=r" (){}[]$*?^|<>\\"):
    """
    Escapes forbidden characters in a given text.

    Args:
        text (str): The input string to process.
        forbidden_chars (str): A string containing characters to escape (default: common special chars).
    
    Returns:
        str: The text with forbidden characters escaped.
    """
    # Create a regex pattern to match any of the forbidden characters
    pattern = f"[{re.escape(forbidden_chars)}]"
    
    # Escape each match by prefixing it with a backslash
    escaped_text = re.sub(pattern, r"\\\g<0>", text)
    
    return escaped_text

# Example usage

    
def main() -> None:
    parser = argparse.ArgumentParser(description='Convert all dictionaries in a folder')
    parser.add_argument('-i', '--input_folder', required=True, help='Input folder containing .tsv and .dfo files')
    parser.add_argument('-o', '--output_folder', required=True, help='Output folder containing dictionary files')
    parser.add_argument('-e', '--extension', default='tab', help='Filename extention for input dictionary files. Default is .tab')
    parser.add_argument('-m', '--metadata', default='dfo', help='Filename extention for input metadata for dictionary. Default is .dfo')
    parser.add_argument('-f', '--filter', help='Filter only dictionary entries with matching keys (seperated by comma)')

    args, array = parser.parse_known_args()

    input_folder = escape_forbidden_chars(args.input_folder)
    output_folder = escape_forbidden_chars(args.output_folder)
    extension = args.extension
    metadata = args.metadata
    dict_filters = args.filter.split(",") if args.filter is not None else []

    if input_folder:
        metafilelist = sorted(glob.glob(input_folder + f'/*.{metadata}'), reverse=True)
        datafilelist = sorted(glob.glob(input_folder + f'/*.{extension}'), reverse=True)
        zippdatafilelist = sorted(glob.glob(input_folder + f'/*.bz2'), reverse=True)

        meta_dict = {}
        data_dict = {}
        print(f'Len of metafilelist: {len(metafilelist)}')
        print(f'Len of datafilelist: {len(datafilelist)}')
        print(f'Len of compressed datafilelist: {len(zippdatafilelist)}')

        # Keep only pairs of metadata and dict data files
        for filepath in metafilelist:
            folder, filename = os.path.split(filepath)
            filebase = filename.split('.')[0]

            meta_dict[filebase] = filepath
        
        bothdatalist = datafilelist+zippdatafilelist

        for filepath in bothdatalist:
            folder, filename = os.path.split(filepath)
            filebase = filename.split('.')[0]

            data_dict[filebase] = filepath

        common_keys = sorted(list(meta_dict.keys() & data_dict.keys()))

        print(common_keys)
        
        metafilelist.clear()
        datafilelist.clear()

        for key in common_keys:
            include_dict = False
            
            if dict_filters:
                for filter in dict_filters:
                    if filter in key:
                        include_dict = True

                        break
            
            if include_dict:
                print(f"Including this dictionary: {key}")
            else:
                continue

            metafilelist.append(meta_dict[key])

            datafile = data_dict[key]

            # If datafile is a .bz2
            if datafile.find('.bz2') >= 0:
                
                cmd_line = f'bzip2 -kd \"{datafile}\"'
                # print(cmd_line)

                if not DEBUG_FLAG:
                    # subprocess.call(cmd_line, shell=True)
                    execute_shell(cmd_line=cmd_line, message=f"bunzip data file")

            datafilelist.append(datafile.replace('.bz2', ''))


        print(f'Len of checked datafilelist: {len(datafilelist)}')
        
    dirs = ['stardict', 'epub', 'kobo', 'lingvo', 'kindle', 'dictd', 'yomitan']

    cmd_line=f'rm -r {output_folder}/*'
    execute_shell(cmd_line=cmd_line, message="Remove existing file in {output_folder}")

    cmd_line=f'rm -r {input_folder}/kindle/*'
    execute_shell(cmd_line=cmd_line, message="Remove existing file in kindle {input_folder}/kindle")

    for dir in dirs:
        cmd_line = f'mkdir -p {output_folder}/{dir}'
        execute_shell(cmd_line=cmd_line, message='Creating directory')
        # subprocess.call(f'mkdir -p {output_folder}/{dir}', shell=True)

    cmd_line = f'mkdir -p {input_folder}/kindle'
    execute_shell(cmd_line=cmd_line, message='Creating directory')
    # subprocess.call(f'rm -r {output_folder}/*', shell=True)

    # use_only_these = {'Tu-dien-ThienChuu-TranVanChanh'}
    for filepath, datafile in zip(metafilelist, datafilelist):
        _, filename = os.path.split(filepath)
        filebase, fileext = os.path.splitext(filename)

        # if filebase not in use_only_these:
        #     continue

        data = readDicInfo(filepath)

        # Add quote to wrap long filename/path
        datafile = datafile.replace(' ', '\\ ')
        dataCreator = data['Owner/Editor'].replace(' ', '\\ ')
        if not dataCreator:
            dataCreator = 'Panthera Tigris'.replace(' ', '\\ ')
            
        dataTarget = data['Target']
        dataSource = data['Source']
        dataFullSource = data['FullSource']
        dataFullTarget = data['FullTarget']
        dataName = escape_forbidden_chars(data["Name"])
        htmlDir = f'kindle'
        htmlOutDir = f'{input_folder}/{htmlDir}'

        if not data:
            continue

        INFLECTION_DIR = './bin/inflections'
        INFLECTION_NONE = 'inflections-none.tab'

        # Generare HTML file for Kindle dictionary
        if 'Inflections' in data and data['Inflections']:
            inflections = f'\"{INFLECTION_DIR}/{data["Inflections"]}\"'
        else:
            inflections = f'{INFLECTION_DIR}/{INFLECTION_NONE}'

        cmd_line = f"python ./bin/tab2opf.py --title={dataName} --source={dataSource} --target={dataTarget} --inflection={inflections} --outdir={htmlOutDir} --creator={dataCreator} --publisher={dataCreator} {datafile}"
        print(cmd_line)
        subprocess.run(shlex.split(cmd_line))

        # Generate .mobi dictionary from opf+html file
        out_path = f'{htmlOutDir}/{filebase}.opf'.replace(' ', '\\ ')
        cmd_line = f"wine ./bin/mobigen/mobigen.exe -unicode -s0 {out_path}"
        print(cmd_line)
        subprocess.run(shlex.split(cmd_line))

        if DEBUG_FLAG:
            continue

        # Move input file to final destinations. Using subprocess.call
        # cmd_line = f'rm *.html *.opf'
        # print(cmd_line)
        # subprocess.call(cmd_line, shell=True)

        cmd_line = f'mv {htmlOutDir}/*.mobi {output_folder}/'
        print(cmd_line)
        subprocess.call(cmd_line, shell=True)

        # Generate other dictionary formats using PyGlossary
        pyglossary = 'pyglossary'
        formats = [
            # DictType, foldername, file ending, need zip
            ('Yomichan', 'yomitan', 'yomitan.zip', False),
            ('Epub2', 'epub', 'epub', False),
            ('Kobo', 'kobo', 'kobo.zip', False),
            ('Stardict', 'stardict', 'ifo', True),
            ('DictOrg', 'dictd', 'index', True),
        ]

        for write_format, folder, extension, needzip in formats:
            _, filename = os.path.split(filepath)
            filebase, _ = os.path.splitext(filename)
            
            out_path = os.path.join(output_folder, folder, f'{filebase}.{extension}')
            cmd_line = f"{pyglossary} --ui=none --read-format=Tabfile --write-format={write_format} " \
                    f"--source-lang={dataSource} --target-lang={dataTarget} --name={dataName} {datafile} {shlex.quote(out_path)}"
            
            execute_shell(cmd_line=cmd_line, message=f"generating {write_format}")

            if needzip:
                out_path = os.path.join(output_folder, f'{folder}/{filebase}.*')
                zip_path = os.path.join(output_folder, f'{filebase}.{folder}.zip')
                cmd_line = f"zip -j {zip_path} {out_path}"

                execute_shell(cmd_line=cmd_line, message=f"creating zip file for {write_format} in {output_folder}")
            else:
                cmd_line = f"mv {out_path} {output_folder}"
                execute_shell(cmd_line=cmd_line, message=f"moving output {out_path} to output folder {output_folder}")

        # Generare Lingvo dictionary
        out_path = os.path.join(output_folder, f'lingvo/{filebase}.dsl').replace(' ', '\\ ') 
        cmd_line = f"ruby ./dsl-tools/tab2dsl/tab2dsl.rb --from-lang {dataFullSource} --to-lang {dataFullTarget} --dict-name {dataName} --output {out_path} {datafile}"
        execute_shell(cmd_line=cmd_line, message=f"generating DSL/Longvo")

        cmd_line = f"mv {out_path}.dz {output_folder}"
        execute_shell(cmd_line=cmd_line, message=f"moving output {out_path} to output folder {output_folder}")
        pass

    dir_formats = [
        ('stardict',  '*.stardict.zip'), 
        ('epub',      '*.epub'),
        ('kobo',      '*.kobo.zip'),
        ('lingvo',    '*.dsl.dz'),
        ('kindle',    '*.mobi'),
        ('dictd',     '*.dictd.zip'),
        ('yomitan',   '*.yomitan.zip'),
    ]

    for dir, format in dir_formats:
        cmd_line = f"zip -9 -j output/all-{dir}.zip output/{format}"
        execute_shell(cmd_line=cmd_line, message=f"Zipping all {dir}-format dicts in {output_folder}")


if __name__ == "__main__":
    main()
