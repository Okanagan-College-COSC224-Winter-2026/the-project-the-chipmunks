@app.route('/practice/test', methods=['GET'])
def practice_test():
    return {'course': 'cosc 224'}, 200
