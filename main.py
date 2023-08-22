import logging
import string
import pandas as pd
from starlette import status
import nltk
from fastapi import FastAPI, UploadFile, HTTPException
from razdel import tokenize
import pymorphy3
from nltk.corpus import stopwords
from starlette.responses import FileResponse

from Dictionary import Dictionary, dictionary_list

app = FastAPI()
FILE_NAME = 'Словарь ключевых слов.xlsx'
HTTP_404_DETAIL = 'для получения информации позвоните по номеру телефона 680-23-76'
nltk.download('stopwords')
ru_stopwords = stopwords.words('russian')
digits = [str(i) for i in range(10)]


@app.on_event("startup")
async def startup():
    logging.basicConfig(level=logging.INFO)
    await load_dictionary()
    logging.info(dictionary_list)


async def load_dictionary():
    df = pd.read_excel(FILE_NAME)
    dictionary_list.clear()
    for index, row in df.iterrows():
        logging.info(row)
        if row['is_run'] is True:
            _price = Dictionary(
                name=row['name'],
                is_run=row['is_run'],
                url=row['url'],
                keywords=row['keywords'].replace(' ', '').replace('\n', '').split(','),
                answer=row['answer'],
            )
            dictionary_list.append(_price)


async def preprocess(question):
    tokens = list(tokenize(question))
    tokens_list = [word.text for word in tokens]
    morph = pymorphy3.MorphAnalyzer()
    return [morph.normal_forms(word)[0]
            for word in tokens_list
            if (word[0] not in digits and
                word not in ru_stopwords and word not in string.punctuation)]


async def search_in_list_keywords(words: list) -> list[Dictionary]:
    score_list: list[(int, Dictionary)] = []
    for dictionary in dictionary_list:
        if dictionary.is_run is False:
            continue
        count_match:int = 0
        for word in words:
            if word in dictionary.keywords:
                count_match += 1
        score_list.append((count_match, dictionary))
    score_list.sort(key=lambda score: score[0])
    score_list.reverse()
    best_of_five: list[(int, Dictionary)] = score_list[:5]
    logging.info(best_of_five)
    if best_of_five[0][0] == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HTTP_404_DETAIL)

    return [dict_with_score[1].dict(exclude={'keywords', 'is_run'}) for dict_with_score in best_of_five if
            dict_with_score[0] != 0]


@app.get("/search_in_dictionary")
async def search_in_dictionary(question: str):
    clear_words = await preprocess(question)
    logging.info(clear_words)
    return await search_in_list_keywords(clear_words)


@app.post("/import_file")
async def add_file(file: UploadFile):
    try:
        contents = file.file.read()
        with open(file.filename, 'wb') as f:
            f.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    await load_dictionary()

    return {"message": f"Successfully uploaded {file.filename}"}


@app.get("/export_file")
async def export_file():
    df = pd.DataFrame(dictionary_list)
    df.to_excel(FILE_NAME, index=False)
    return FileResponse(path=FILE_NAME, filename=FILE_NAME, media_type='multipart/form-data')


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
