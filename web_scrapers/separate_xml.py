import pandas as pd

def save_as_files(df):
    for item in df.iterrows():
        file_name = item[1]['index'] + '.xml' 
        xml = item[1]['xml']
        f =  open('../French_Comedies/TEI_files/' + item[1]['index'] + '.xml', 'w')
        f.write(xml)
        f.close()

def main():
	metadata = pd.read_csv('../French_Comedies/French_Comedies.tsv', sep='\t')
	theater_df = metadata[metadata.url.str.count('theatre-classique')>0]
	url_to_index_dict = dict(zip(theater_df['url'].tolist(), theater_df['index'].tolist()))
	crawled_xml_df = pd.read_json('../French_Comedies/xml_plays.jsl', lines=True)
	crawled_xml_df['index'] = crawled_xml_df['url'].map(url_to_index_dict)
	save_as_files(crawled_xml_df)


if __name__ == '__main__':
	main()