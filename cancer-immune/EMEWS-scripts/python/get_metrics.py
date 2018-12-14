import os, sys, glob

def get_tumor_cell_count(instance_dir):
    """
    @return tumor cell count value from fname or -2, if file doesn't exist, or
    -1 if run terminated prematurely.
    """
    tumor_cell_count = '-2'
    fname = '{}/output/metrics.txt'.format(instance_dir)
    if os.path.exists(fname):
        with open(fname) as f_in:
            tumor_cell_count = '-1'
            line = f_in.readlines()[-1].strip()
            items = line.split("\t")
            if len(items) > 1 and items[0] == '30240':
                tumor_cell_count = items[1]

    return tumor_cell_count

def main(root_dir, upf, results_file):
    import pandas as pd

    df = pd.read_csv(upf)
    df['instance'] = df.index + 1
    df['tumor_cell_count'] = -2

    files = glob.glob('{}/instance_*'.format(root_dir))
    for f in files:
        instance = int(f[f.rfind("_") + 1 :])
        count = int(get_tumor_cell_count(f))
        df.ix[instance - 1, 'tumor_cell_count'] = count
        #print('{} {}: {}'.format(instance, f, count))
        #print(df.head())

    df.to_csv(results_file, index=False)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
