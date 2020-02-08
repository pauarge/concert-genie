import React from 'react';
import BpkButton from 'bpk-component-button';
import {colors} from 'bpk-tokens/tokens/base.es6';
import {withButtonAlignment} from "bpk-component-icon";
import LongArrowRightIconSm from "bpk-component-icon/sm/long-arrow-right";
import BpkSectionList from "bpk-component-section-list";
import BpkSectionListSection from "bpk-component-section-list/src/BpkSectionListSection";
import BpkSectionListItem from "bpk-component-section-list/src/BpkSectionListItem";
import BpkAutosuggestSuggestion from "bpk-component-autosuggest/src/BpkAutosuggestSuggestion";
import BpkAutosuggest from "bpk-component-autosuggest/src/BpkAutosuggest";

const doneInterval = 250;

const AlignedArrow = withButtonAlignment(LongArrowRightIconSm);

const getSuggestionValue = item => item;

const renderSuggestion = suggestion => (
  <BpkAutosuggestSuggestion
    value={suggestion}
    indent={suggestion.indent}
  />
);

class Search extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      value: '',
      suggestions: [],
      typingTimer: null,
      results: []
    };

    this.handleSubmit = this.handleSubmit.bind(this);
    this.getSuggestions = this.getSuggestions.bind(this);
  }

  getSuggestions(val) {
    if (this.state.value.length > 2) {
      fetch("http://localhost:5000/suggest?artist=" + val)
        .then(res => res.json())
        .then(
          (result) => {
            console.log(result);
            this.setState({
              suggestions: result,
            });
          },
          error => console.log(error)
        )
    }
  }

  handleSubmit(event) {
    event.preventDefault();
    fetch("http://localhost:5000/?artist=" + this.state.value)
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            results: result,
          });
        },
        error => console.log(error)
      )
  }

  onChange = (e, {newValue}) => {
    this.setState({
      value: newValue,
    });
  };

  onSuggestionsFetchRequested = ({value}) => {
    clearTimeout(this.state.typingTimer);
    this.setState({
      typingTimer: setTimeout(() => this.getSuggestions(value), doneInterval)
    });
  };

  onSuggestionsClearRequested = () => {
    this.setState({
      suggestions: [],
    });
  };

  render() {
    const {value, suggestions} = this.state;

    const inputProps = {
      id: 'my-autosuggest',
      name: 'my-autosuggest',
      placeholder: 'Start typing an artist name...',
      value,
      onChange: this.onChange,
    };

    return (
      <>
        <form onSubmit={this.handleSubmit}>
          <p>
            <div>
              <BpkAutosuggest
                suggestions={suggestions}
                onSuggestionsFetchRequested={this.onSuggestionsFetchRequested}
                onSuggestionsClearRequested={this.onSuggestionsClearRequested}
                getSuggestionValue={getSuggestionValue}
                renderSuggestion={renderSuggestion}
                inputProps={inputProps}
              />
            </div>
          </p>
          <p>
            <BpkButton submit={true}>
              Search&nbsp;
              <AlignedArrow fill={colors.colorWhite}/>
            </BpkButton>
          </p>
        </form>
        {this.state.results.length > 0 &&
        <p>
          <BpkSectionList>
            <BpkSectionListSection headerText="Songs">
              {this.state.results.map(i => <BpkSectionListItem>{i}</BpkSectionListItem>)}
            </BpkSectionListSection>
          </BpkSectionList>
        </p>}
      </>);
  }
}

export default Search;
