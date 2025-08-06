from openai import OpenAI

def test():
    client = OpenAI(
        base_url='https://ms-fc-1d889e1e-d2ad.api-inference.modelscope.cn/v1',
        api_key='ms-e9cb1ee1-d248-4f05-87d1-fbc2083c41ae', # ModelScope Token
    )

    response = client.embeddings.create(
        model='Qwen/Qwen3-Embedding-4B-GGUF', # ModelScope Model-Id
        input='你好',
        encoding_format="float"
    )

    print(response)

if __name__ == '__main__':
    test()