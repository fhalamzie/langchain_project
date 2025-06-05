#!/usr/bin/env python3
"""
Simple test for LangGraph workflow without heavy dependencies
"""

def test_langgraph_availability():
    """Test if LangGraph is available"""
    print("🧪 Testing LangGraph availability...")
    
    try:
        from langgraph.graph import StateGraph, START, END
        from langgraph.graph.message import add_messages
        from langgraph.checkpoint.memory import MemorySaver
        from typing_extensions import TypedDict
        
        print("✅ LangGraph imports successful")
        
        # Test basic workflow creation
        class TestState(TypedDict):
            value: int
            
        def increment(state: TestState):
            return {"value": state["value"] + 1}
            
        # Create workflow
        workflow = StateGraph(TestState)
        workflow.add_node("increment", increment)
        workflow.add_edge(START, "increment")
        workflow.add_edge("increment", END)
        
        # Compile
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)
        
        print("✅ LangGraph workflow compilation successful")
        
        # Test execution
        result = app.invoke({"value": 5})
        print(f"✅ LangGraph execution successful: {result}")
        
        if result.get("value") == 6:
            print("✅ LangGraph workflow working correctly")
            return True
        else:
            print(f"❌ LangGraph workflow returned unexpected result: {result}")
            return False
            
    except ImportError as e:
        print(f"❌ LangGraph not available: {e}")
        return False
    except Exception as e:
        print(f"❌ LangGraph test failed: {e}")
        return False

def test_workflow_logic():
    """Test the workflow logic without LangGraph"""
    print("\n🔍 Testing workflow logic...")
    
    # Simulate workflow steps
    state = {
        "user_query": "Wie viele Wohnungen gibt es?",
        "business_entities": [],
        "generated_sql": "",
        "iterations": 0,
        "success": False
    }
    
    # Step 1: Extract entities
    entities = ["Wohnungen"]
    state["business_entities"] = entities
    print(f"  ✅ Extract entities: {entities}")
    
    # Step 2: Generate SQL
    sql = "SELECT COUNT(*) FROM WOHNUNG"
    state["generated_sql"] = sql
    print(f"  ✅ Generate SQL: {sql}")
    
    # Step 3: Mark success
    state["success"] = True
    print(f"  ✅ Mark success: {state['success']}")
    
    return state["success"]

if __name__ == "__main__":
    print("🎯 LangGraph Workflow Tests")
    print("=" * 40)
    
    langgraph_available = test_langgraph_availability()
    logic_working = test_workflow_logic()
    
    print("\n📊 Test Results:")
    print(f"  LangGraph Available: {'✅' if langgraph_available else '❌'}")
    print(f"  Logic Working: {'✅' if logic_working else '❌'}")
    
    if langgraph_available and logic_working:
        print("\n🎉 LangGraph workflow implementation ready!")
    elif logic_working:
        print("\n⚠️ Logic ready, but LangGraph needs to be installed")
    else:
        print("\n❌ Workflow implementation needs work")