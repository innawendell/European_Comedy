import pandas as pd

def save_as_files(df):
    for item in df.iterrows():
        #print(df.head())
        file_name = item[1]['index'] + '.xml'
        xml = item[1]['xml']
        f =  open('../Contrastive_Material/TEI_files/' + item[1]['index'] + '.xml', 'w')
        f.write(xml)
        f.close()

def main():
    metadata_df = pd.read_csv('../Contrastive_Material/shakespeare.tsv', sep='\t')
    url_to_index_dict = dict(zip(metadata_df['url'].tolist(), metadata_df['index'].tolist()))
    crawled_xml_df = pd.read_json('../Contrastive_Material/shakespeare_xml_plays.jsl', lines=True)
    crawled_xml_df['index'] = crawled_xml_df['url'].map(url_to_index_dict)
    save_as_files(crawled_xml_df)


if __name__ == '__main__':
	main()