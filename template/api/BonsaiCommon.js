// Define source or sink in documentation by checking for an explicit Category tag. If the class does not provide one,
// check the inheritance tree of the class. If the class inherits Bonsai.Sink and Bonsai.Combinator, ignore the Bonsai.Sink
// inheritance overrides the Bonsai.Combinator inheritance for determining whether an operator is a source or a combinator. This
// is because maybe sink operators inherit Bonsai.Combinator in addition to Bonsai.Sink.

exports.defineOperatorType = function defineOperatorType(model){
    let operatorType = {'source': false, 'sink': false, 'combinator': false};
    if (model.syntax && model.syntax.content[0].value){
      if (model.syntax.content[0].value.includes('[WorkflowElementCategory(ElementCategory.Source)]')){
        operatorType.source = true;
      }
      else if (model.syntax.content[0].value.includes('[WorkflowElementCategory(ElementCategory.Sink)]')){
        operatorType.sink = true;
      }
      else if (model.syntax.content[0].value.includes('[WorkflowElementCategory(ElementCategory.Combinator)]')){
        operatorType.combinator = true;
      }
    }
    if (!(operatorType.source || operatorType.sink || operatorType.combinator)){
      if (model.inheritance){
        const inheritanceLength = model.inheritance.length;
        for (let i = 0; i < inheritanceLength; i++){
          if (model.inheritance[i].uid.includes('Bonsai.Source')){
            operatorType.source = true;
          }
          else if (model.inheritance[i].uid.includes('Bonsai.Sink')){
            operatorType.sink = true;
          }
          else if (model.inheritance[i].uid.includes('Bonsai.Combinator')){
            operatorType.combinator = true;
          }
          if (model.inheritance[i].uid.includes('OpenEphys.Onix1.MultiDeviceFactory')){
            operatorType.hub = true;
          }
          else if (model.inheritance[i].uid.includes('OpenEphys.Onix1.SingleDeviceFactory')){
            operatorType.device = true;
          }
        }
      }
    }
    operatorType.showWorkflow = operatorType.source | operatorType.sink | operatorType.combinator;
    return operatorType;
  }

