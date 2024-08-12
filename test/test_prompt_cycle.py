# TODO: fix this test, and add more tests utilizing @fixture
from prompt_cycle import main

def test_prompt_cycle():
    main('data/text.txt', 'core_example.py', '--prompt "generate a response to this text"', '--yes')
    assert True
    return
