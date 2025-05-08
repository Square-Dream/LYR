from konlpy.tag import Okt

try:
    okt = Okt()
    print(okt.morphs("테스트 중입니다."))
except Exception as e:
    print(f"Error: {e}")
