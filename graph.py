import numpy as np
import matplotlib.pyplot as plt

def draw(result, N):
    title = str(N+1)+'-gram'
    plt.title(title)
    plt.xlabel('Ranking')
    plt.ylabel('Correct answer rate (cumulated) [%]')
    plt.ylim(0, 100)
    plt.grid(True)
    result = np.array(result)
    total = result.sum()
    print(total)
    left = np.array([i+1 for i in range(len(result))])
    height = np.array(result.cumsum()/total) * 100
    plt.bar(left[:-2], height[:-2])
    count = 0
    for x, y in zip(left[:-2], height[:-2]):
        plt.text(x, y, str(int(round(height[count], 0))), ha='center', va='bottom', fontsize=7)
        count += 1
    plt.savefig(f'graphs/{title}.jpg')

draw([4138, 1108, 433, 495, 106, 118, 78, 64, 95, 24, 67, 13, 24, 14, 31, 9, 20, 15, 8, 43, 11, 8, 16, 35, 30, 8, 6, 8, 5, 6, 7321], 3)